from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar

from django.conf import settings
from django.db import transaction
from django.db.models import Model
from django.db.models.query_utils import Q
from django.db.models.signals import m2m_changed, post_save, pre_delete
from dramatiq.actor import Actor

from authentik.core.models import Group, User
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
    token = _CTX_INHIBIT_DISPATCH.set(True)
    try:
        yield
    finally:
        _CTX_INHIBIT_DISPATCH.reset(token)


def _assigned_provider_filter() -> Q:
    return Q(backchannel_application__isnull=False) | Q(application__isnull=False)


def _has_assigned_provider(provider_type: type[OutgoingSyncProvider]) -> bool:
    return provider_type.objects.filter(_assigned_provider_filter()).exists()


def _dispatch_on_commit(callback: Callable[[], None]) -> None:
    if settings.TEST:
        callback()
        return
    transaction.on_commit(callback)


def register_signals(
    provider_type: type[OutgoingSyncProvider],
    task_sync_direct_dispatch: Actor[[str, str | int], None],
    task_sync_delete_dispatch: Actor[[str, list[tuple[str, str]]], None],
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
        if not _has_assigned_provider(provider_type):
            return
        model_path = class_to_path(instance.__class__)
        instance_pk = instance.pk
        _dispatch_on_commit(
            lambda: task_sync_direct_dispatch.send_with_options(
                args=(model_path, instance_pk),
                uid=f"{model_path}:{instance_pk}:direct-dispatch",
                deduplicate_by_uid=True,
            )
        )

    post_save.connect(model_post_save, User, dispatch_uid=uid, weak=False)
    post_save.connect(model_post_save, Group, dispatch_uid=uid, weak=False)

    def model_pre_delete(sender: type[Model], instance: User | Group, **_):
        """Pre-delete handler"""
        if _CTX_INHIBIT_DISPATCH.get():
            return
        mappings = provider_type.get_object_mappings(instance)
        if not mappings:
            return
        model_path = class_to_path(instance.__class__)
        _dispatch_on_commit(
            lambda: task_sync_delete_dispatch.send(
                model_path,
                mappings,
            )
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
        if not _has_assigned_provider(provider_type):
            return
        instance_pk = instance.pk
        pk_list = list(pk_set)
        _dispatch_on_commit(
            lambda: task_sync_m2m_dispatch.send(instance_pk, action, pk_list, reverse)
        )

    m2m_changed.connect(model_m2m_changed, User.groups.through, dispatch_uid=uid, weak=False)
