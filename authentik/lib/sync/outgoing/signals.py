from collections.abc import Iterable
from typing import Any, TypeVar
from uuid import UUID

from django.db.models.signals import m2m_changed, post_save, pre_delete
from dramatiq.actor import Actor

from authentik.core.models import Group, User
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider
from authentik.lib.utils.reflection import class_to_path

ModelT = TypeVar("ModelT", bound=User | Group)


def register_signals(
    provider_type: type[OutgoingSyncProvider],
    task_sync_direct_dispatch: Actor[[str, Any, str], None],
    task_sync_m2m_dispatch: Actor[[Any, str, list[Any], bool], None],
) -> None:
    """Register sync signals"""
    uid = class_to_path(provider_type)

    def model_post_save(
        sender: type[ModelT],
        instance: ModelT,
        created: bool,
        update_fields: Iterable[str] | None = None,
        **_: Any,
    ) -> None:
        """Post save handler"""
        # Special case for user object; don't start sync task when we've only updated `last_login`
        # This primarily happens during user login
        if sender == User and update_fields == {"last_login"}:
            return
        task_sync_direct_dispatch.send(
            class_to_path(instance.__class__),
            instance.pk,
            Direction.add.value,
        )

    post_save.connect(model_post_save, User, dispatch_uid=uid, weak=False)
    post_save.connect(model_post_save, Group, dispatch_uid=uid, weak=False)

    def model_pre_delete(sender: type[ModelT], instance: ModelT, **_: Any) -> None:
        """Pre-delete handler"""
        task_sync_direct_dispatch.send(
            class_to_path(instance.__class__),
            instance.pk,
            Direction.remove.value,
        )

    pre_delete.connect(model_pre_delete, User, dispatch_uid=uid, weak=False)
    pre_delete.connect(model_pre_delete, Group, dispatch_uid=uid, weak=False)

    def model_m2m_changed(
        sender: type[ModelT],
        instance: ModelT,
        action: str,
        pk_set: set[int | UUID],
        reverse: bool,
        **_: Any,
    ) -> None:
        """Sync group membership"""
        if action not in ["post_add", "post_remove"]:
            return
        task_sync_m2m_dispatch.send(instance.pk, action, list(pk_set), reverse)

    m2m_changed.connect(model_m2m_changed, User.ak_groups.through, dispatch_uid=uid, weak=False)
