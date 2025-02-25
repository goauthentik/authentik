from collections.abc import Callable
from dataclasses import asdict

from celery.exceptions import Retry
from celery.result import allow_join_result
from django.core.paginator import Paginator
from django.db.models import Model, QuerySet
from django.db.models.query import Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.expression.exceptions import SkipObjectException
from authentik.core.models import Group, User
from authentik.events.logs import LogEvent
from authentik.events.models import TaskStatus
from authentik.events.system_tasks import SystemTask
from authentik.events.utils import sanitize_item
from authentik.lib.sync.outgoing import PAGE_SIZE, PAGE_TIMEOUT
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.exceptions import (
    BadRequestSyncException,
    DryRunRejected,
    StopSync,
    TransientSyncException,
)
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider
from authentik.lib.utils.reflection import class_to_path, path_to_class


class SyncTasks:
    """Container for all sync 'tasks' (this class doesn't actually contain celery
    tasks due to celery's magic, however exposes a number of functions to be called from tasks)"""

    logger: BoundLogger

    def __init__(self, provider_model: type[OutgoingSyncProvider]) -> None:
        super().__init__()
        self._provider_model = provider_model

    def sync_all(self, single_sync: Callable[[int], None]):
        for provider in self._provider_model.objects.filter(
            Q(backchannel_application__isnull=False) | Q(application__isnull=False)
        ):
            self.trigger_single_task(provider, single_sync)

    def trigger_single_task(self, provider: OutgoingSyncProvider, sync_task: Callable[[int], None]):
        """Wrapper single sync task that correctly sets time limits based
        on the amount of objects that will be synced"""
        users_paginator = Paginator(provider.get_object_qs(User), PAGE_SIZE)
        groups_paginator = Paginator(provider.get_object_qs(Group), PAGE_SIZE)
        soft_time_limit = (users_paginator.num_pages + groups_paginator.num_pages) * PAGE_TIMEOUT
        time_limit = soft_time_limit * 1.5
        return sync_task.apply_async(
            (provider.pk,), time_limit=int(time_limit), soft_time_limit=int(soft_time_limit)
        )

    def sync_single(
        self,
        task: SystemTask,
        provider_pk: int,
        sync_objects: Callable[[int, int], list[str]],
    ):
        self.logger = get_logger().bind(
            provider_type=class_to_path(self._provider_model),
            provider_pk=provider_pk,
        )
        provider = self._provider_model.objects.filter(
            Q(backchannel_application__isnull=False) | Q(application__isnull=False),
            pk=provider_pk,
        ).first()
        if not provider:
            return
        task.set_uid(slugify(provider.name))
        messages = []
        messages.append(_("Starting full provider sync"))
        self.logger.debug("Starting provider sync")
        users_paginator = Paginator(provider.get_object_qs(User), PAGE_SIZE)
        groups_paginator = Paginator(provider.get_object_qs(Group), PAGE_SIZE)
        with allow_join_result(), provider.sync_lock as lock_acquired:
            if not lock_acquired:
                self.logger.debug("Failed to acquire sync lock, skipping", provider=provider.name)
                return
            try:
                for page in users_paginator.page_range:
                    messages.append(_("Syncing page {page} of users".format(page=page)))
                    for msg in sync_objects.apply_async(
                        args=(class_to_path(User), page, provider_pk),
                        time_limit=PAGE_TIMEOUT,
                        soft_time_limit=PAGE_TIMEOUT,
                    ).get():
                        messages.append(LogEvent(**msg))
                for page in groups_paginator.page_range:
                    messages.append(_("Syncing page {page} of groups".format(page=page)))
                    for msg in sync_objects.apply_async(
                        args=(class_to_path(Group), page, provider_pk),
                        time_limit=PAGE_TIMEOUT,
                        soft_time_limit=PAGE_TIMEOUT,
                    ).get():
                        messages.append(LogEvent(**msg))
            except TransientSyncException as exc:
                self.logger.warning("transient sync exception", exc=exc)
                raise task.retry(exc=exc) from exc
            except StopSync as exc:
                task.set_error(exc)
                return
        task.set_status(TaskStatus.SUCCESSFUL, *messages)

    def sync_objects(
        self, object_type: str, page: int, provider_pk: int, override_dry_run=False, **filter
    ):
        _object_type = path_to_class(object_type)
        self.logger = get_logger().bind(
            provider_type=class_to_path(self._provider_model),
            provider_pk=provider_pk,
            object_type=object_type,
        )
        messages = []
        provider = self._provider_model.objects.filter(pk=provider_pk).first()
        if not provider:
            return messages
        # Override dry run mode if requested, however don't save the provider
        # so that scheduled sync tasks still run in dry_run mode
        if override_dry_run:
            provider.dry_run = False
        try:
            client = provider.client_for_model(_object_type)
        except TransientSyncException:
            return messages
        paginator = Paginator(provider.get_object_qs(_object_type).filter(**filter), PAGE_SIZE)
        if client.can_discover:
            self.logger.debug("starting discover")
            client.discover()
        self.logger.debug("starting sync for page", page=page)
        for obj in paginator.page(page).object_list:
            obj: Model
            try:
                client.write(obj)
            except SkipObjectException:
                self.logger.debug("skipping object due to SkipObject", obj=obj)
                continue
            except DryRunRejected as exc:
                messages.append(
                    asdict(
                        LogEvent(
                            _("Dropping mutating request due to dry run"),
                            log_level="info",
                            logger=f"{provider._meta.verbose_name}@{object_type}",
                            attributes={
                                "obj": sanitize_item(obj),
                                "method": exc.method,
                                "url": exc.url,
                                "body": exc.body,
                            },
                        )
                    )
                )
            except BadRequestSyncException as exc:
                self.logger.warning("failed to sync object", exc=exc, obj=obj)
                messages.append(
                    asdict(
                        LogEvent(
                            _(
                                (
                                    "Failed to sync {object_type} {object_name} "
                                    "due to error: {error}"
                                ).format_map(
                                    {
                                        "object_type": obj._meta.verbose_name,
                                        "object_name": str(obj),
                                        "error": str(exc),
                                    }
                                )
                            ),
                            log_level="warning",
                            logger=f"{provider._meta.verbose_name}@{object_type}",
                            attributes={"arguments": exc.args[1:], "obj": sanitize_item(obj)},
                        )
                    )
                )
            except TransientSyncException as exc:
                self.logger.warning("failed to sync object", exc=exc, user=obj)
                messages.append(
                    asdict(
                        LogEvent(
                            _(
                                (
                                    "Failed to sync {object_type} {object_name} "
                                    "due to transient error: {error}"
                                ).format_map(
                                    {
                                        "object_type": obj._meta.verbose_name,
                                        "object_name": str(obj),
                                        "error": str(exc),
                                    }
                                )
                            ),
                            log_level="warning",
                            logger=f"{provider._meta.verbose_name}@{object_type}",
                            attributes={"obj": sanitize_item(obj)},
                        )
                    )
                )
            except StopSync as exc:
                self.logger.warning("Stopping sync", exc=exc)
                messages.append(
                    asdict(
                        LogEvent(
                            _(
                                "Stopping sync due to error: {error}".format_map(
                                    {
                                        "error": exc.detail(),
                                    }
                                )
                            ),
                            log_level="warning",
                            logger=f"{provider._meta.verbose_name}@{object_type}",
                            attributes={"obj": sanitize_item(obj)},
                        )
                    )
                )
                break
        return messages

    def sync_signal_direct(self, model: str, pk: str | int, raw_op: str):
        self.logger = get_logger().bind(
            provider_type=class_to_path(self._provider_model),
        )
        model_class: type[Model] = path_to_class(model)
        instance = model_class.objects.filter(pk=pk).first()
        if not instance:
            return
        operation = Direction(raw_op)
        for provider in self._provider_model.objects.filter(
            Q(backchannel_application__isnull=False) | Q(application__isnull=False)
        ):
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
            except TransientSyncException as exc:
                raise Retry() from exc
            except SkipObjectException:
                continue
            except StopSync as exc:
                self.logger.warning(exc, provider_pk=provider.pk)

    def sync_signal_m2m(self, group_pk: str, action: str, pk_set: list[int]):
        self.logger = get_logger().bind(
            provider_type=class_to_path(self._provider_model),
        )
        group = Group.objects.filter(pk=group_pk).first()
        if not group:
            return
        for provider in self._provider_model.objects.filter(
            Q(backchannel_application__isnull=False) | Q(application__isnull=False)
        ):
            # Check if the object is allowed within the provider's restrictions
            queryset: QuerySet = provider.get_object_qs(Group)
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
            except TransientSyncException as exc:
                raise Retry() from exc
            except SkipObjectException:
                continue
            except StopSync as exc:
                self.logger.warning(exc, provider_pk=provider.pk)
