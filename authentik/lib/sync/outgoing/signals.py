
from django.core.paginator import Paginator
from django.db.models import Model
from django.db.models.query import Q
from django.db.models.signals import m2m_changed, post_save, pre_delete

from authentik.core.models import Group, User
from authentik.lib.sync.outgoing import PAGE_SIZE, PAGE_TIMEOUT
from authentik.lib.sync.outgoing.base import Direction
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider
from authentik.lib.utils.reflection import class_to_path
from authentik.tasks.tasks import async_task, result


def register_signals(
    provider_type: type[OutgoingSyncProvider],
    task_sync_single: str,
    task_sync_direct: str,
    task_sync_m2m: str,
):
    """Register sync signals"""
    uid = class_to_path(provider_type)

    def post_save_provider(sender: type[Model], instance: OutgoingSyncProvider, created: bool, **_):
        """Trigger sync when Provider is saved"""
        users_paginator = Paginator(instance.get_object_qs(User), PAGE_SIZE)
        groups_paginator = Paginator(instance.get_object_qs(Group), PAGE_SIZE)
        timeout = (users_paginator.num_pages + groups_paginator.num_pages) * PAGE_TIMEOUT * 1.5
        async_task(task_sync_single, instance.pk, q_options={"timeout": timeout})

    post_save.connect(post_save_provider, provider_type, dispatch_uid=uid, weak=False)

    def model_post_save(sender: type[Model], instance: User | Group, created: bool, **_):
        """Post save handler"""
        if not provider_type.objects.filter(
            Q(backchannel_application__isnull=False) | Q(application__isnull=False)
        ).exists():
            return
        async_task(
            task_sync_direct, class_to_path(instance.__class__), instance.pk, Direction.add.value
        )

    post_save.connect(model_post_save, User, dispatch_uid=uid, weak=False)
    post_save.connect(model_post_save, Group, dispatch_uid=uid, weak=False)

    def model_pre_delete(sender: type[Model], instance: User | Group, **_):
        """Pre-delete handler"""
        if not provider_type.objects.filter(
            Q(backchannel_application__isnull=False) | Q(application__isnull=False)
        ).exists():
            return
        result(
            async_task(
                task_sync_direct,
                class_to_path(instance.__class__),
                instance.pk,
                Direction.remove.value,
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
        if not provider_type.objects.filter(
            Q(backchannel_application__isnull=False) | Q(application__isnull=False)
        ).exists():
            return
        # reverse: instance is a Group, pk_set is a list of user pks
        # non-reverse: instance is a User, pk_set is a list of groups
        if reverse:
            async_task(task_sync_m2m, str(instance.pk), action, list(pk_set))
        else:
            for group_pk in pk_set:
                async_task(task_sync_m2m, group_pk, action, [instance.pk])

    m2m_changed.connect(model_m2m_changed, User.ak_groups.through, dispatch_uid=uid, weak=False)
