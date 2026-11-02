"""SCIM provider signals"""

from itertools import batched

from django.db import transaction
from django.db.models import Q
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver

from authentik.core.models import Application, Group, User
from authentik.lib.sync.outgoing.signals import register_signals, sync_outgoing_dispatch_inhibited
from authentik.policies.models import PolicyBinding
from authentik.providers.scim.models import SCIMProvider
from authentik.providers.scim.tasks import (
    SCOPE_SYNC_PAGE_SIZE,
    scim_sync_delete_dispatch,
    scim_sync_direct_dispatch,
    scim_sync_m2m_dispatch,
    scim_sync_scope,
    scim_sync_scope_dispatch,
)
from authentik.tasks.models import Task, TaskStatus

register_signals(
    SCIMProvider,
    task_sync_direct_dispatch=scim_sync_direct_dispatch,
    task_sync_delete_dispatch=scim_sync_delete_dispatch,
    task_sync_m2m_dispatch=scim_sync_m2m_dispatch,
)


def _queue_scope_for_targets(target_pks):
    """Coalesce queued sweeps while locking their consumption until access changes commit."""
    with transaction.atomic():
        providers = (
            SCIMProvider.objects.filter(backchannel_application_id__in=target_pks)
            .only("pk")
            .order_by("pk")
            .select_for_update(of=("self",))
        )
        for provider in providers:
            uid = f"{provider.pk}:scope"
            pending = Task.objects.select_for_update().filter(
                actor_name=scim_sync_scope_dispatch.actor_name,
                _uid=uid,
                state=TaskStatus.QUEUED,
            )
            if not pending.exists():
                scim_sync_scope_dispatch.send_with_options(
                    args=(provider.pk,), rel_obj=provider, uid=uid
                )


def _providers_for_groups(group_pks):
    groups = Group.objects.filter(pk__in=group_pks).with_ancestors()
    return (
        SCIMProvider.objects.filter(backchannel_application__bindings__enabled=True)
        .filter(
            Q(backchannel_application__bindings__group__in=groups)
            | Q(backchannel_application__bindings__policy__isnull=False)
        )
        .only("pk")
        .distinct()
    )


@receiver(pre_save, sender=PolicyBinding)
def scim_binding_pre_save(sender, instance: PolicyBinding, raw=False, **_):
    """Remember both applications when a binding is moved or its access rules change."""
    if raw or sync_outgoing_dispatch_inhibited():
        return
    fields = (
        "target_id",
        "policy_id",
        "group_id",
        "user_id",
        "enabled",
        "negate",
        "dry_run",
        "order",
        "timeout",
        "failure_result",
        "expiring",
        "expires",
    )
    current = {field: getattr(instance, field) for field in fields}
    previous = (
        PolicyBinding.objects.filter(pk=instance.pk).values(*fields).first()
        if not instance._state.adding
        else None
    )
    instance._scim_scope_targets = set()
    if previous == current:
        return
    instance._scim_scope_targets.add(instance.target_id)
    if previous:
        instance._scim_scope_targets.add(previous["target_id"])


@receiver(post_save, sender=PolicyBinding)
def scim_binding_post_save(sender, instance: PolicyBinding, raw=False, **_):
    """Binding changes can affect every user, including default access without bindings."""
    if raw or sync_outgoing_dispatch_inhibited():
        return
    _queue_scope_for_targets(getattr(instance, "_scim_scope_targets", {instance.target_id}))


@receiver(post_delete, sender=PolicyBinding)
def scim_binding_post_delete(sender, instance: PolicyBinding, **_):
    """Reconcile access after the binding has actually been removed."""
    if not sync_outgoing_dispatch_inhibited():
        _queue_scope_for_targets({instance.target_id})


@receiver(pre_save, sender=Application)
def scim_application_pre_save(sender, instance: Application, raw=False, update_fields=None, **_):
    """Only policy-engine mode changes require a scope sweep on application save."""
    if raw or sync_outgoing_dispatch_inhibited() or instance._state.adding:
        return
    instance._scim_scope_changed = False
    if update_fields is not None and "policy_engine_mode" not in update_fields:
        return
    previous = (
        Application.objects.filter(pk=instance.pk)
        .values_list("policy_engine_mode", flat=True)
        .first()
    )
    instance._scim_scope_changed = previous != instance.policy_engine_mode


@receiver(post_save, sender=Application)
def scim_application_post_save(sender, instance: Application, raw=False, **_):
    """Evaluate the application's saved mode, not the previous value."""
    if (
        not raw
        and not sync_outgoing_dispatch_inhibited()
        and getattr(instance, "_scim_scope_changed", False)
    ):
        _queue_scope_for_targets({instance.pk})


@receiver(m2m_changed, sender=User.groups.through)
def scim_application_membership_changed(
    sender, instance: User | Group, action: str, pk_set: set | None, reverse: bool, **_
):
    """Only reevaluate affected users and applications, independently of exported groups."""
    if sync_outgoing_dispatch_inhibited():
        return
    if action == "pre_clear":
        if not SCIMProvider.objects.filter(backchannel_application__isnull=False).exists():
            return
        related = instance.users if reverse else instance.groups
        instance._scim_clear_pks = list(related.values_list("pk", flat=True))
        return
    if action == "post_clear":
        pk_set = instance.__dict__.pop("_scim_clear_pks", [])
        for page in batched(pk_set, SCOPE_SYNC_PAGE_SIZE, strict=False):
            scim_sync_m2m_dispatch.send(instance.pk, "post_remove", list(page), reverse)
    elif action not in {"post_add", "post_remove"}:
        return
    if not pk_set:
        return
    group_pks = [instance.pk] if reverse else pk_set
    user_pks = pk_set if reverse else [instance.pk]
    for provider in _providers_for_groups(group_pks):
        for page in batched(user_pks, SCOPE_SYNC_PAGE_SIZE, strict=False):
            scim_sync_scope.send_with_options(
                args=(provider.pk, list(page)),
                rel_obj=provider,
                uid=f"{provider.pk}:scope:{page[0]}",
            )


@receiver(m2m_changed, sender=Group.parents.through)
def scim_group_parentage_changed(
    sender, instance: Group, action: str, pk_set: set | None, reverse: bool, **_
):
    """Changing group ancestry changes access for users in the child subtree."""
    if sync_outgoing_dispatch_inhibited():
        return
    if action == "pre_clear":
        if not SCIMProvider.objects.filter(backchannel_application__isnull=False).exists():
            return
        related = instance.children if reverse else instance.parents
        instance._scim_parentage_clear_pks = list(related.values_list("pk", flat=True))
        return
    if action == "post_clear":
        pk_set = instance.__dict__.pop("_scim_parentage_clear_pks", [])
    elif action not in {"post_add", "post_remove"}:
        return
    if not pk_set:
        return
    parent_pks = [instance.pk] if reverse else pk_set
    child_pks = pk_set if reverse else [instance.pk]
    children = Group.objects.filter(pk__in=child_pks).with_descendants()
    users = User.objects.filter(groups__in=children).values_list("pk", flat=True).distinct()
    for provider in _providers_for_groups(parent_pks):
        for page in batched(users.iterator(), SCOPE_SYNC_PAGE_SIZE, strict=False):
            scim_sync_scope.send_with_options(
                args=(provider.pk, list(page)),
                rel_obj=provider,
                uid=f"{provider.pk}:scope:{page[0]}",
            )
