from collections.abc import Callable

from celery.result import allow_join_result
from django.core.paginator import Paginator
from django.db.models import Model, QuerySet
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from structlog.stdlib import BoundLogger, get_logger
from tenant_schemas_celery.task import TenantTask

from authentik.core.models import Group, User
from authentik.events.models import TaskStatus
from authentik.events.system_tasks import SystemTask
from authentik.lib.sync.outgoing import PAGE_SIZE, PAGE_TIMEOUT
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.exceptions import StopSync, TransientSyncException
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider
from authentik.lib.utils.reflection import class_to_path, path_to_class


class SyncAllTask(TenantTask):
    """Task to trigger a sync in all providers, usually scheduled"""

    def __init__(
        self, provider_model: type[OutgoingSyncProvider], single_sync: Callable[[int], None]
    ) -> None:
        super().__init__()
        self._provider_model = provider_model
        self._single_sync = single_sync

    def run(self):
        for provider in self._provider_model.objects.filter(backchannel_application__isnull=False):
            self._single_sync.delay(provider.pk)


class SyncSingleTask(SystemTask):
    """Task to trigger sync of all providers, triggered by SyncAllTask or on signal"""

    def __init__(
        self,
        provider_model: type[OutgoingSyncProvider],
        sync_users: Callable[[int, int], list[str]],
        sync_groups: Callable[[int, int], list[str]],
    ) -> None:
        super().__init__()
        self._provider_model = provider_model
        self._sync_users = sync_users
        self._sync_groups = sync_groups

    def run(self, provider_pk: int):
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
        messages.append(_("Starting full provider sync"))
        self.logger.debug("Starting provider sync")
        users_paginator = Paginator(provider.get_object_qs(User), PAGE_SIZE)
        groups_paginator = Paginator(provider.get_object_qs(Group), PAGE_SIZE)
        self.soft_time_limit = self.time_limit = (
            users_paginator.count + groups_paginator.count
        ) * PAGE_TIMEOUT
        with allow_join_result():
            try:
                for page in users_paginator.page_range:
                    messages.append(_("Syncing page %(page)d of users" % {"page": page}))
                    for msg in self._sync_users.delay(page, provider_pk).get():
                        messages.append(msg)
                for page in groups_paginator.page_range:
                    messages.append(_("Syncing page %(page)d of groups" % {"page": page}))
                    for msg in self._sync_groups.delay(page, provider_pk).get():
                        messages.append(msg)
            except StopSync as exc:
                self.set_error(exc)
                return
        self.set_status(TaskStatus.SUCCESSFUL, *messages)


class SyncObjectTask(TenantTask):
    """Sync a specified object (user/group)"""

    logger: BoundLogger

    def __init__(
        self, provider_model: type[OutgoingSyncProvider], object_type: type[User | Group]
    ) -> None:
        super().__init__()
        self._provider_model = provider_model
        self._object_type = object_type
        self.soft_time_limit = PAGE_TIMEOUT
        self.time_limit = PAGE_TIMEOUT

    def run(self, page: int, provider_pk: int):
        self.logger = get_logger().bind(
            provider_type=class_to_path(self._provider_model),
            provider_pk=provider_pk,
            object_type=class_to_path(self._object_type),
        )
        messages = []
        provider = self._provider_model.objects.filter(pk=provider_pk).first()
        if not provider:
            return messages
        try:
            client = provider.client_for_model(self._object_type)
        except TransientSyncException:
            return messages
        paginator = Paginator(provider.get_object_qs(self._object_type), PAGE_SIZE)
        self.logger.debug("starting sync for page", page=page)
        for obj in paginator.page(page).object_list:
            obj: Model
            try:
                client.write(obj)
            except TransientSyncException as exc:
                self.logger.warning("failed to sync object", exc=exc, user=obj)
                messages.append(
                    _(
                        (
                            "Failed to sync {object_type} {object_name} "
                            "due to remote error: {error}"
                        ).format_map(
                            {
                                "object_type": obj._meta.verbose_name,
                                "object_name": str(obj),
                                "error": exc.detail(),
                            }
                        )
                    )
                )
            except StopSync as exc:
                self.logger.warning("Stopping sync", exc=exc)
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


class SyncSignalDirectTask(TenantTask):
    """Handler for post_save and pre_delete signal"""

    logger: BoundLogger

    def __init__(self, provider_model: type[OutgoingSyncProvider]) -> None:
        super().__init__()
        self._provider_model = provider_model

    def run(self, model: str, pk: str | int, raw_op: str):
        self.logger = get_logger().bind(
            provider_type=class_to_path(self._provider_model),
        )
        model_class: type[Model] = path_to_class(model)
        instance = model_class.objects.filter(pk=pk).first()
        if not instance:
            return
        operation = Direction(raw_op)
        for provider in self._provider_model.objects.filter(backchannel_application__isnull=False):
            client = provider.client_for_model(instance.__class__)
            # Check if the object is allowed within the provider's restrictions
            queryset = provider.get_object_qs(instance.__class__)
            if not queryset:
                continue

            # The queryset we get from the provider must include the instance we've got given
            # otherwise ignore this provider
            if not queryset.filter(pk=instance.pk).exists():
                continue

            try:
                if operation == Direction.add:
                    client.write(instance)
                if operation == Direction.remove:
                    client.delete(instance)
            except (StopSync, TransientSyncException) as exc:
                self.logger.warning(exc, provider_pk=provider.pk)


class SyncSignalM2MTask(TenantTask):
    """Update m2m (group membership)"""

    logger: BoundLogger

    def __init__(self, provider_model: type[OutgoingSyncProvider]) -> None:
        super().__init__()
        self._provider_model = provider_model

    def run(self, group_pk: str, action: str, pk_set: list[int]):
        self.logger = get_logger().bind(
            provider_type=class_to_path(self._provider_model),
        )
        group = Group.objects.filter(pk=group_pk).first()
        if not group:
            return
        for provider in self._provider_model.objects.filter(backchannel_application__isnull=False):
            # Check if the object is allowed within the provider's restrictions
            queryset: QuerySet = provider.get_group_qs()
            # The queryset we get from the provider must include the instance we've got given
            # otherwise ignore this provider
            if not queryset.filter(pk=group_pk).exists():
                continue

            client = provider.client_for_model(Group)
            try:
                operation = None
                if action == "post_add":
                    operation = Direction.add
                if action == "post_remove":
                    operation = Direction.remove
                client.update_group(group, operation, pk_set)
            except (StopSync, TransientSyncException) as exc:
                self.logger.warning(exc, provider_pk=provider.pk)
