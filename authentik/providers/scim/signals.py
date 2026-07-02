"""SCIM provider signals"""

from django.db.models.signals import m2m_changed

from authentik.core.models import Group, User
from authentik.lib.sync.outgoing.signals import register_signals, sync_outgoing_dispatch_inhibited
from authentik.providers.scim.models import SCIMProvider
from authentik.providers.scim.tasks import (
    scim_sync,
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


def scim_application_policy_membership_changed(
    sender: type,
    instance: User | Group,
    action: str,
    pk_set: set,
    reverse: bool,
    **_,
):
    """Sync SCIM providers when a group-bound application policy changes user scope."""
    if action not in ["post_add", "post_remove"]:
        return
    if sync_outgoing_dispatch_inhibited():
        return

    if reverse:
        group_pks = [instance.pk]
    else:
        group_pks = pk_set
    if not group_pks:
        return

    groups = Group.objects.filter(pk__in=group_pks).with_ancestors()
    providers = SCIMProvider.objects.filter(
        backchannel_application__bindings__enabled=True,
        backchannel_application__bindings__group__in=groups,
    ).distinct()
    for provider in providers:
        scim_sync.send_with_options(
            args=(provider.pk,),
            rel_obj=provider,
            uid=(
                f"{provider.name}:application-policy-groups:{action}:"
                f"{sorted(str(group_pk) for group_pk in group_pks)}"
            ),
            time_limit=provider.get_sync_time_limit_ms(),
        )


m2m_changed.connect(
    scim_application_policy_membership_changed,
    sender=User.groups.through,
    dispatch_uid="authentik.providers.scim.signals.application_policy_membership",
    weak=False,
)
