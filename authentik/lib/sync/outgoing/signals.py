from django.db.models import Model
from django.db.models.query import Q
from django.db.models.signals import m2m_changed, post_save, pre_delete
from dramatiq.actor import Actor
from dramatiq.results.errors import ResultFailure

from authentik.core.models import Group, User
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider
from authentik.lib.utils.reflection import class_to_path


def register_signals(
    provider_type: type[OutgoingSyncProvider],
    task_sync_direct: Actor,
    task_sync_m2m: Actor,
):
    """Register sync signals"""
    uid = class_to_path(provider_type)

    def model_post_save(sender: type[Model], instance: User | Group, created: bool, **_):
        """Post save handler"""
        for provider in provider_type.objects.filter(
            Q(backchannel_application__isnull=False) | Q(application__isnull=False)
        ):
            task_sync_direct.send_with_options(
                args=(
                    class_to_path(instance.__class__),
                    instance.pk,
                    provider.pk,
                    Direction.add.value,
                ),
                rel_obj=provider,
            )

    post_save.connect(model_post_save, User, dispatch_uid=uid, weak=False)
    post_save.connect(model_post_save, Group, dispatch_uid=uid, weak=False)

    def model_pre_delete(sender: type[Model], instance: User | Group, **_):
        """Pre-delete handler"""
        for provider in provider_type.objects.filter(
            Q(backchannel_application__isnull=False) | Q(application__isnull=False)
        ):
            task_sync_direct.send_with_options(
                args=(
                    class_to_path(instance.__class__),
                    instance.pk,
                    provider.pk,
                    Direction.remove.value,
                ),
                rel_obj=provider,
            )

    pre_delete.connect(model_pre_delete, User, dispatch_uid=uid, weak=False)
    pre_delete.connect(model_pre_delete, Group, dispatch_uid=uid, weak=False)

    def model_m2m_changed(
        sender: type[Model], instance, action: str, pk_set: set, reverse: bool, **kwargs
    ):
        """Sync group membership"""
        if action not in ["post_add", "post_remove"]:
            return
        for provider in provider_type.objects.filter(
            Q(backchannel_application__isnull=False) | Q(application__isnull=False)
        ):
            # reverse: instance is a Group, pk_set is a list of user pks
            # non-reverse: instance is a User, pk_set is a list of groups
            if reverse:
                task_sync_m2m.send_with_options(
                    args=(instance.pk, provider.pk, action, list(pk_set)),
                    rel_obj=provider,
                )
            else:
                for group_pk in pk_set:
                    task_sync_m2m.send_with_options(
                        args=(group_pk, provider.pk, action, [instance.pk]),
                        rel_obj=provider,
                    )

    m2m_changed.connect(model_m2m_changed, User.ak_groups.through, dispatch_uid=uid, weak=False)
