from collections.abc import Callable

from celery.result import allow_join_result
from django.core.paginator import Paginator
from django.db.models import Model
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from structlog.stdlib import get_logger
from tenant_schemas_celery.task import TenantTask

from authentik.events.models import TaskStatus
from authentik.events.system_tasks import SystemTask
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.providers.scim.clients import PAGE_SIZE, PAGE_TIMEOUT
from authentik.providers.scim.clients.exceptions import SCIMRequestException
from authentik.providers.scim.clients.group import SCIMGroupClient
from authentik.providers.scim.clients.user import SCIMUserClient
from authentik.providers.scim.models import SCIMProvider
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()


class SyncAllTask(TenantTask):

    def __init__(self, provider_model: type[Model], single_sync: Callable[[int], None]) -> None:
        super().__init__()
        self._provider_model = provider_model
        self._single_sync = single_sync

    def run(self):
        for provider in self._provider_model.objects.filter(backchannel_application__isnull=False):
            self._single_sync.delay(provider.pk)


class SyncSingleTask(SystemTask):

    def __init__(self, provider_model: type[Model]) -> None:
        super().__init__()
        self._provider_model = provider_model

    def run(self, provider_pk, *args, **kwargs):
        provider = self._provider_model.objects.filter(
            pk=provider_pk, backchannel_application__isnull=False
        ).first()
        if not provider:
            return
        lock = provider.sync_lock
        if lock.locked():
            self.logger.debug("Sync locked, skipping task", source=provider.name)
            return
        self.set_uid(slugify(provider.name))
        messages = []
        messages.append(_("Starting full SCIM sync"))
        self.logger.debug("Starting SCIM sync")
        users_paginator = Paginator(provider.get_user_qs(), PAGE_SIZE)
        groups_paginator = Paginator(provider.get_group_qs(), PAGE_SIZE)
        self.soft_time_limit = self.time_limit = (
            users_paginator.count + groups_paginator.count
        ) * PAGE_TIMEOUT
        with allow_join_result():
            try:
                for page in users_paginator.page_range:
                    messages.append(_("Syncing page %(page)d of users" % {"page": page}))
                    for msg in scim_sync_users.delay(page, provider_pk).get():
                        messages.append(msg)
                for page in groups_paginator.page_range:
                    messages.append(_("Syncing page %(page)d of groups" % {"page": page}))
                    for msg in scim_sync_group.delay(page, provider_pk).get():
                        messages.append(msg)
            except StopSync as exc:
                self.set_error(exc)
                return
        self.set_status(TaskStatus.SUCCESSFUL, *messages)


@CELERY_APP.task(
    soft_time_limit=PAGE_TIMEOUT,
    task_time_limit=PAGE_TIMEOUT,
)
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
                    "Failed to sync user {user_name} due to remote error: {error}".format_map(
                        {
                            "user_name": user.username,
                            "error": exc.detail(),
                        }
                    )
                )
            )
        except StopSync as exc:
            LOGGER.warning("Stopping sync", exc=exc)
            messages.append(
                _(
                    "Stopping sync due to error: {error}".format_map(
                        {
                            "error": exc.detail(),
                        }
                    )
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
                    "Failed to sync group {group_name} due to remote error: {error}".format_map(
                        {
                            "group_name": group.name,
                            "error": exc.detail(),
                        }
                    )
                )
            )
        except StopSync as exc:
            LOGGER.warning("Stopping sync", exc=exc)
            messages.append(
                _(
                    "Stopping sync due to error: {error}".format_map(
                        {
                            "error": exc.detail(),
                        }
                    )
                )
            )
            break
    return messages
