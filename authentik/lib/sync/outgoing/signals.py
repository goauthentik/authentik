from contextlib import contextmanager
from contextvars import ContextVar

from django.db.models import Model
from django.db.models.signals import m2m_changed, post_save, pre_delete
from dramatiq.actor import Actor

from authentik.core.models import Group, User
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider
from authentik.lib.utils.reflection import class_to_path

_CTX_INHIBIT_DISPATCH = ContextVar[bool](
    "authentik_sync_outgoing_inhibit_dispatch",
    default=False,
)


@contextmanager
def sync_outgoing_inhibit_dispatch():
    """
    Prevent direct and m2m tasks from being dispatched when User/Group/membership change
    """
    _CTX_INHIBIT_DISPATCH.set(True)
    try:
        yield
    finally:
        _CTX_INHIBIT_DISPATCH.set(False)


def register_signals(
    provider_type: type[OutgoingSyncProvider],
    task_sync_direct_dispatch: Actor[[str, str | int, str], None],
    task_sync_m2m_dispatch: Actor[[str, str, list[str], bool], None],
):
    """Register sync signals"""
    uid = class_to_path(provider_type)

    def model_post_save(
        sender: type[Model],
        instance: User | Group,
        created: bool,
        update_fields: list[str] | None = None,
        **_,
    ):
        """Post save handler"""
        # Special case for user object; don't start sync task when we've only updated `last_login`
        # This primarily happens during user login
        if sender == User and update_fields == {"last_login"}:
            return
        if _CTX_INHIBIT_DISPATCH.get():
            return
        if not provider_type.objects.exists():
            return
        task_sync_direct_dispatch.send(
            class_to_path(instance.__class__),
            instance.pk,
            Direction.add.value,
        )

    post_save.connect(model_post_save, User, dispatch_uid=uid, weak=False)
    post_save.connect(model_post_save, Group, dispatch_uid=uid, weak=False)

    def model_pre_delete(sender: type[Model], instance: User | Group, **_):
        """Pre-delete handler"""
        if _CTX_INHIBIT_DISPATCH.get():
            return
        if not provider_type.objects.exists():
            return
        task_sync_direct_dispatch.send(
            class_to_path(instance.__class__),
            instance.pk,
            Direction.remove.value,
        )

    pre_delete.connect(model_pre_delete, User, dispatch_uid=uid, weak=False)
    pre_delete.connect(model_pre_delete, Group, dispatch_uid=uid, weak=False)

    def model_m2m_changed(
        sender: type[Model], instance, action: str, pk_set: set, reverse: bool, **kwargs
    ):
        """Sync group membership"""
        if action not in ["post_add", "post_remove"]:
            return
        if _CTX_INHIBIT_DISPATCH.get():
            return
        if not provider_type.objects.exists():
            return
        task_sync_m2m_dispatch.send(instance.pk, action, list(pk_set), reverse)

    m2m_changed.connect(model_m2m_changed, User.ak_groups.through, dispatch_uid=uid, weak=False)
