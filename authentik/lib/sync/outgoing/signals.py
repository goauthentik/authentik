from collections.abc import Callable

from django.db.models import Model
from django.db.models.signals import m2m_changed, post_save, pre_delete

from authentik.core.models import Group, User
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider
from authentik.lib.utils.reflection import class_to_path


def register_signals(
    provider_type: type[OutgoingSyncProvider],
    task_sync_single: Callable[[int], None],
    task_sync_direct: Callable[[int], None],
    task_sync_m2m: Callable[[int], None],
):
    """Register sync signals"""
    uid = class_to_path(provider_type)

    def post_save_provider(sender: type[Model], instance, created: bool, **_):
        """Trigger sync when Provider is saved"""
        task_sync_single.delay(instance.pk)

    post_save.connect(post_save_provider, provider_type, dispatch_uid=uid)

    def model_post_save(sender: type[Model], instance: User | Group, created: bool, **_):
        """Post save handler"""
        if not provider_type.objects.filter(backchannel_application__isnull=False).exists():
            return
        task_sync_direct.delay(class_to_path(instance.__class__), instance.pk, Direction.add.value)

    post_save.connect(model_post_save, User, dispatch_uid=uid)
    post_save.connect(model_post_save, Group, dispatch_uid=uid)

    def model_pre_delete(sender: type[Model], instance: User | Group, **_):
        """Pre-delete handler"""
        if not provider_type.objects.filter(backchannel_application__isnull=False).exists():
            return
        task_sync_direct.delay(
            class_to_path(instance.__class__), instance.pk, Direction.remove.value
        )

    pre_delete.connect(model_pre_delete, User, dispatch_uid=uid)
    pre_delete.connect(model_pre_delete, Group, dispatch_uid=uid)

    def model_m2m_changed(
        sender: type[Model], instance, action: str, pk_set: set, reverse: bool, **kwargs
    ):
        """Sync group membership"""
        if action not in ["post_add", "post_remove"]:
            return
        if not provider_type.objects.filter(backchannel_application__isnull=False).exists():
            return
        # reverse: instance is a Group, pk_set is a list of user pks
        # non-reverse: instance is a User, pk_set is a list of groups
        if reverse:
            task_sync_m2m.delay(str(instance.pk), action, list(pk_set))
        else:
            for group_pk in pk_set:
                task_sync_m2m.delay(group_pk, action, [instance.pk])

    m2m_changed.connect(model_m2m_changed, User.ak_groups.through, dispatch_uid=uid)
