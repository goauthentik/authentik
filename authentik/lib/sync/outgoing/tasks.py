from django.core.paginator import Paginator
from django.db.models import Model, QuerySet
from django.db.models.query import Q
from django.utils.text import slugify
from dramatiq.actor import Actor
from dramatiq.composition import group
from dramatiq.errors import Retry
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.expression.exceptions import SkipObjectException
from authentik.core.models import Group, User
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
from authentik.tasks.middleware import CurrentTask
from authentik.tasks.models import Task


class SyncTasks:
    """Container for all sync 'tasks' (this class doesn't actually contain
    tasks due to dramatiq's magic, however exposes a number of functions to be called from tasks)"""

    logger: BoundLogger

    def __init__(self, provider_model: type[OutgoingSyncProvider]) -> None:
        super().__init__()
        self._provider_model = provider_model

    def sync_paginator(
        self,
        current_task: Task,
        provider: OutgoingSyncProvider,
        sync_objects: Actor,
        paginator: Paginator,
        object_type: type[User | Group],
        **options,
    ):
        tasks = []
        for page in paginator.page_range:
            page_sync = sync_objects.message_with_options(
                args=(class_to_path(object_type), page, provider.pk),
                time_limit=PAGE_TIMEOUT * 1000,
                # Assign tasks to the same schedule as the current one
                rel_obj=current_task.rel_obj,
                **options,
            )
            tasks.append(page_sync)
        return tasks

    def sync(
        self,
        provider_pk: int,
        sync_objects: Actor,
    ):
        task = CurrentTask.get_task()
        self.logger = get_logger().bind(
            provider_type=class_to_path(self._provider_model),
            provider_pk=provider_pk,
        )
        provider: OutgoingSyncProvider = self._provider_model.objects.filter(
            Q(backchannel_application__isnull=False) | Q(application__isnull=False),
            pk=provider_pk,
        ).first()
        if not provider:
            return
        task.set_uid(slugify(provider.name))
        task.info("Starting full provider sync")
        self.logger.debug("Starting provider sync")
        with provider.sync_lock as lock_acquired:
            if not lock_acquired:
                self.logger.debug("Failed to acquire sync lock, skipping", provider=provider.name)
                return
            try:
                users_tasks = group(
                    self.sync_paginator(
                        current_task=task,
                        provider=provider,
                        sync_objects=sync_objects,
                        paginator=provider.get_paginator(User),
                        object_type=User,
                    )
                )
                group_tasks = group(
                    self.sync_paginator(
                        current_task=task,
                        provider=provider,
                        sync_objects=sync_objects,
                        paginator=provider.get_paginator(Group),
                        object_type=Group,
                    )
                )
                users_tasks.run().wait(timeout=provider.get_object_sync_time_limit(User))
                group_tasks.run().wait(timeout=provider.get_object_sync_time_limit(Group))
            except TransientSyncException as exc:
                self.logger.warning("transient sync exception", exc=exc)
                raise Retry() from exc
            except StopSync as exc:
                task.error(exc)
                return

    def sync_objects(
        self,
        object_type: str,
        page: int,
        provider_pk: int,
        override_dry_run=False,
        **filter,
    ):
        task = CurrentTask.get_task()
        _object_type: type[Model] = path_to_class(object_type)
        self.logger = get_logger().bind(
            provider_type=class_to_path(self._provider_model),
            provider_pk=provider_pk,
            object_type=object_type,
        )
        task.info(f"Syncing page {page} of {_object_type._meta.verbose_name_plural}")
        provider: OutgoingSyncProvider = self._provider_model.objects.filter(
            Q(backchannel_application__isnull=False) | Q(application__isnull=False),
            pk=provider_pk,
        ).first()
        if not provider:
            return
        # Override dry run mode if requested, however don't save the provider
        # so that scheduled sync tasks still run in dry_run mode
        if override_dry_run:
            provider.dry_run = False
        try:
            client = provider.client_for_model(_object_type)
        except TransientSyncException:
            return
        paginator = Paginator(provider.get_object_qs(_object_type).filter(**filter), PAGE_SIZE)
        if client.can_discover:
            self.logger.debug("starting discover")
            client.discover()
        self.logger.debug("starting sync for page", page=page)
        task.info(f"Syncing page {page} or {_object_type._meta.verbose_name_plural}")
        for obj in paginator.page(page).object_list:
            obj: Model
            try:
                client.write(obj)
            except SkipObjectException:
                self.logger.debug("skipping object due to SkipObject", obj=obj)
                continue
            except DryRunRejected as exc:
                task.info(
                    "Dropping mutating request due to dry run",
                    attributes={
                        "obj": sanitize_item(obj),
                        "method": exc.method,
                        "url": exc.url,
                        "body": exc.body,
                    },
                )
            except BadRequestSyncException as exc:
                self.logger.warning("failed to sync object", exc=exc, obj=obj)
                task.warning(
                    f"Failed to sync {obj._meta.verbose_name} {str(obj)} due to error: {str(exc)}",
                    attributes={"arguments": exc.args[1:], "obj": sanitize_item(obj)},
                )
            except TransientSyncException as exc:
                self.logger.warning("failed to sync object", exc=exc, user=obj)
                task.warning(
                    f"Failed to sync {obj._meta.verbose_name} {str(obj)} due to "
                    "transient error: {str(exc)}",
                    attributes={"obj": sanitize_item(obj)},
                )
            except StopSync as exc:
                self.logger.warning("Stopping sync", exc=exc)
                task.warning(
                    f"Stopping sync due to error: {exc.detail()}",
                    attributes={"obj": sanitize_item(obj)},
                )
                break

    def sync_signal_direct(
        self,
        model: str,
        pk: str | int,
        provider_pk: int,
        raw_op: str,
    ):
        self.logger = get_logger().bind(
            provider_type=class_to_path(self._provider_model),
        )
        model_class: type[Model] = path_to_class(model)
        instance = model_class.objects.filter(pk=pk).first()
        if not instance:
            return
        provider: OutgoingSyncProvider = self._provider_model.objects.filter(
            Q(backchannel_application__isnull=False) | Q(application__isnull=False),
            pk=provider_pk,
        ).first()
        if not provider:
            return
        operation = Direction(raw_op)
        client = provider.client_for_model(instance.__class__)
        # Check if the object is allowed within the provider's restrictions
        queryset = provider.get_object_qs(instance.__class__)
        if not queryset:
            return

        # The queryset we get from the provider must include the instance we've got given
        # otherwise ignore this provider
        if not queryset.filter(pk=instance.pk).exists():
            return

        try:
            if operation == Direction.add:
                client.write(instance)
            if operation == Direction.remove:
                client.delete(instance)
        except TransientSyncException as exc:
            raise Retry() from exc
        except SkipObjectException:
            return
        except DryRunRejected as exc:
            self.logger.info("Rejected dry-run event", exc=exc)
        except StopSync as exc:
            self.logger.warning("Stopping sync", exc=exc, provider_pk=provider.pk)

    def sync_signal_m2m(
        self,
        group_pk: str,
        provider_pk: int,
        action: str,
        pk_set: list[int],
    ):
        self.logger = get_logger().bind(
            provider_type=class_to_path(self._provider_model),
        )
        group = Group.objects.filter(pk=group_pk).first()
        if not group:
            return
        provider: OutgoingSyncProvider = self._provider_model.objects.filter(
            Q(backchannel_application__isnull=False) | Q(application__isnull=False),
            pk=provider_pk,
        ).first()
        if not provider:
            return

        # Check if the object is allowed within the provider's restrictions
        queryset: QuerySet = provider.get_object_qs(Group)
        # The queryset we get from the provider must include the instance we've got given
        # otherwise ignore this provider
        if not queryset.filter(pk=group_pk).exists():
            return

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
            return
        except DryRunRejected as exc:
            self.logger.info("Rejected dry-run event", exc=exc)
        except StopSync as exc:
            self.logger.warning("Stopping sync", exc=exc, provider_pk=provider.pk)
