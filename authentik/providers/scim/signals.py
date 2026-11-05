"""SCIM provider signals"""

from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver

from authentik.core.models import Application, Group, User
from authentik.lib.sync.outgoing.signals import (
    register_signals,
    sync_outgoing_dispatch_is_inhibited,
)
from authentik.policies.models import PolicyBinding
from authentik.providers.scim.models import SCIMProvider
from authentik.providers.scim.tasks import (
    queue_cleared_memberships,
    queue_scope_for_membership,
    queue_scope_for_parentage,
    queue_scope_for_targets,
    scim_sync_delete_dispatch,
    scim_sync_direct_dispatch,
    scim_sync_m2m_dispatch,
)

register_signals(
    SCIMProvider,
    task_sync_direct_dispatch=scim_sync_direct_dispatch,
    task_sync_delete_dispatch=scim_sync_delete_dispatch,
    task_sync_m2m_dispatch=scim_sync_m2m_dispatch,
)


@receiver(pre_save, sender=PolicyBinding)
def scim_binding_pre_save(sender, instance: PolicyBinding, raw=False, **_):
    """Remember both applications when a binding is moved or its access rules change."""
    if raw or sync_outgoing_dispatch_is_inhibited():
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
    if raw or sync_outgoing_dispatch_is_inhibited():
        return
    queue_scope_for_targets(getattr(instance, "_scim_scope_targets", {instance.target_id}))


@receiver(post_delete, sender=PolicyBinding)
def scim_binding_post_delete(sender, instance: PolicyBinding, **_):
    """Reconcile access after the binding has actually been removed."""
    if not sync_outgoing_dispatch_is_inhibited():
        queue_scope_for_targets({instance.target_id})


@receiver(pre_save, sender=Application)
def scim_application_pre_save(sender, instance: Application, raw=False, update_fields=None, **_):
    """Only policy-engine mode changes require a scope sweep on application save."""
    if raw or sync_outgoing_dispatch_is_inhibited() or instance._state.adding:
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
        and not sync_outgoing_dispatch_is_inhibited()
        and getattr(instance, "_scim_scope_changed", False)
    ):
        queue_scope_for_targets({instance.pk})


@receiver(m2m_changed, sender=User.groups.through)
def scim_application_membership_changed(
    sender, instance: User | Group, action: str, pk_set: set | None, reverse: bool, **_
):
    """Only reevaluate affected users and applications, independently of exported groups."""
    if sync_outgoing_dispatch_is_inhibited():
        return
    if action == "pre_clear":
        if not SCIMProvider.objects.filter(backchannel_application__isnull=False).exists():
            return
        related = instance.users if reverse else instance.groups
        instance._scim_clear_pks = list(related.values_list("pk", flat=True))
        return
    if action == "post_clear":
        pk_set = instance.__dict__.pop("_scim_clear_pks", [])
        queue_cleared_memberships(instance.pk, pk_set, reverse)
    elif action not in {"post_add", "post_remove"}:
        return
    if not pk_set:
        return
    group_pks = [instance.pk] if reverse else pk_set
    user_pks = pk_set if reverse else [instance.pk]
    queue_scope_for_membership(group_pks, user_pks)


@receiver(m2m_changed, sender=Group.parents.through)
def scim_group_parentage_changed(
    sender, instance: Group, action: str, pk_set: set | None, reverse: bool, **_
):
    """Changing group ancestry changes access for users in the child subtree."""
    if sync_outgoing_dispatch_is_inhibited():
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
    queue_scope_for_parentage(parent_pks, child_pks)
