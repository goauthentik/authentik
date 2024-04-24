"""SCIM Provider tasks"""

from typing import Any

from django.db.models import Model, QuerySet
from pydanticscim.responses import PatchOp
from structlog.stdlib import get_logger

from authentik.core.models import Group, User
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.lib.sync.outgoing.tasks import SyncAllTask, SyncSingleTask
from authentik.lib.utils.reflection import path_to_class
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.exceptions import SCIMRequestException
from authentik.providers.scim.clients.group import SCIMGroupClient
from authentik.providers.scim.clients.user import SCIMUserClient
from authentik.providers.scim.models import SCIMProvider
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()


def client_for_model(provider: SCIMProvider, model: Model) -> SCIMClient:
    """Get SCIM client for model"""
    if isinstance(model, User):
        return SCIMUserClient(provider)
    if isinstance(model, Group):
        return SCIMGroupClient(provider)
    raise ValueError(f"Invalid model {model}")


scim_sync = CELERY_APP.register_task(SyncSingleTask(SCIMProvider))
scim_sync_all = CELERY_APP.register_task(SyncAllTask(SCIMProvider, scim_sync))


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
        queryset: QuerySet | None = None
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
