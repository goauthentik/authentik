"""SCIM Provider tasks"""
from typing import Any, Optional

from celery.result import allow_join_result
from django.core.paginator import Paginator
from django.db.models import Model, QuerySet
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from pydanticscim.responses import PatchOp
from structlog.stdlib import get_logger

from authentik.core.models import Group, User
from authentik.events.monitored_tasks import MonitoredTask, TaskResult, TaskResultStatus
from authentik.lib.utils.reflection import path_to_class
from authentik.providers.scim.clients import PAGE_SIZE
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.exceptions import SCIMRequestException, StopSync
from authentik.providers.scim.clients.group import SCIMGroupClient
from authentik.providers.scim.clients.user import SCIMUserClient
from authentik.providers.scim.models import SCIMProvider
from authentik.root.celery import CELERY_APP

LOGGER = get_logger(__name__)


def client_for_model(provider: SCIMProvider, model: Model) -> SCIMClient:
    """Get SCIM client for model"""
    if isinstance(model, User):
        return SCIMUserClient(provider)
    if isinstance(model, Group):
        return SCIMGroupClient(provider)
    raise ValueError(f"Invalid model {model}")


@CELERY_APP.task()
def scim_sync_all():
    """Run sync for all providers"""
    for provider in SCIMProvider.objects.filter(backchannel_application__isnull=False):
        scim_sync.delay(provider.pk)


@CELERY_APP.task(bind=True, base=MonitoredTask)
def scim_sync(self: MonitoredTask, provider_pk: int) -> None:
    """Run SCIM full sync for provider"""
    provider: SCIMProvider = SCIMProvider.objects.filter(pk=provider_pk).first()
    if not provider:
        return
    self.set_uid(slugify(provider.name))
    result = TaskResult(TaskResultStatus.SUCCESSFUL, [])
    result.messages.append(_("Starting full SCIM sync"))
    LOGGER.debug("Starting SCIM sync")
    users_paginator = Paginator(provider.get_user_qs(), PAGE_SIZE)
    groups_paginator = Paginator(provider.get_group_qs(), PAGE_SIZE)
    with allow_join_result():
        try:
            for page in users_paginator.page_range:
                result.messages.append(_("Syncing page %(page)d of users" % {"page": page}))
                for msg in scim_sync_users.delay(page, provider_pk).get():
                    result.messages.append(msg)
            for page in groups_paginator.page_range:
                result.messages.append(_("Syncing page %(page)d of groups" % {"page": page}))
                for msg in scim_sync_group.delay(page, provider_pk).get():
                    result.messages.append(msg)
        except StopSync as exc:
            self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
            return
    self.set_status(result)


@CELERY_APP.task()
def scim_sync_users(page: int, provider_pk: int):
    """Sync single or multiple users to SCIM"""
    messages = []
    provider: SCIMProvider = SCIMProvider.objects.filter(pk=provider_pk).first()
    if not provider:
        return messages
    try:
        client = SCIMUserClient(provider)
    except SCIMRequestException:
        return messages
    paginator = Paginator(provider.get_user_qs(), PAGE_SIZE)
    LOGGER.debug("starting user sync for page", page=page)
    for user in paginator.page(page).object_list:
        try:
            client.write(user)
        except SCIMRequestException as exc:
            LOGGER.warning("failed to sync user", exc=exc, user=user)
            messages.append(
                _(
                    "Failed to sync user due to remote error %(name)s: %(error)s"
                    % {
                        "name": user.username,
                        "error": str(exc),
                    }
                )
            )
        except StopSync as exc:
            LOGGER.warning("Stopping sync", exc=exc)
            messages.append(
                _(
                    "Stopping sync due to error: %(error)s"
                    % {
                        "error": str(exc),
                    }
                )
            )
            break
    return messages


@CELERY_APP.task()
def scim_sync_group(page: int, provider_pk: int):
    """Sync single or multiple groups to SCIM"""
    messages = []
    provider: SCIMProvider = SCIMProvider.objects.filter(pk=provider_pk).first()
    if not provider:
        return messages
    try:
        client = SCIMGroupClient(provider)
    except SCIMRequestException:
        return messages
    paginator = Paginator(provider.get_group_qs(), PAGE_SIZE)
    LOGGER.debug("starting group sync for page", page=page)
    for group in paginator.page(page).object_list:
        try:
            client.write(group)
        except SCIMRequestException as exc:
            LOGGER.warning("failed to sync group", exc=exc, group=group)
            messages.append(
                _(
                    "Failed to sync group due to remote error %(name)s: %(error)s"
                    % {
                        "name": group.name,
                        "error": str(exc),
                    }
                )
            )
        except StopSync as exc:
            LOGGER.warning("Stopping sync", exc=exc)
            messages.append(
                _(
                    "Stopping sync due to error: %(error)s"
                    % {
                        "error": str(exc),
                    }
                )
            )
            break
    return messages


@CELERY_APP.task()
def scim_signal_direct(model: str, pk: Any, raw_op: str):
    """Handler for post_save and pre_delete signal"""
    model_class: type[Model] = path_to_class(model)
    instance = model_class.objects.filter(pk=pk).first()
    if not instance:
        return
    operation = PatchOp(raw_op)
    for provider in SCIMProvider.objects.filter(backchannel_application__isnull=False):
        client = client_for_model(provider, instance)
        # Check if the object is allowed within the provider's restrictions
        queryset: Optional[QuerySet] = None
        if isinstance(instance, User):
            queryset = provider.get_user_qs()
        if isinstance(instance, Group):
            queryset = provider.get_group_qs()
        if not queryset:
            continue

        # The queryset we get from the provider must include the instance we've got given
        # otherwise ignore this provider
        if not queryset.filter(pk=instance.pk).exists():
            continue

        try:
            if operation == PatchOp.add:
                client.write(instance)
            if operation == PatchOp.remove:
                client.delete(instance)
        except (StopSync, SCIMRequestException) as exc:
            LOGGER.warning(exc)


@CELERY_APP.task()
def scim_signal_m2m(group_pk: str, action: str, pk_set: list[int]):
    """Update m2m (group membership)"""
    group = Group.objects.filter(pk=group_pk).first()
    if not group:
        return
    for provider in SCIMProvider.objects.filter(backchannel_application__isnull=False):
        # Check if the object is allowed within the provider's restrictions
        queryset: QuerySet = provider.get_group_qs()
        # The queryset we get from the provider must include the instance we've got given
        # otherwise ignore this provider
        if not queryset.filter(pk=group_pk).exists():
            continue

        client = SCIMGroupClient(provider)
        try:
            operation = None
            if action == "post_add":
                operation = PatchOp.add
            if action == "post_remove":
                operation = PatchOp.remove
            client.update_group(group, operation, pk_set)
        except (StopSync, SCIMRequestException) as exc:
            LOGGER.warning(exc)
