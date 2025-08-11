"""Microsoft Entra Provider tasks"""

from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor

from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProvider
from authentik.lib.sync.outgoing.tasks import SyncTasks

sync_tasks = SyncTasks(MicrosoftEntraProvider)


@actor(description=_("Sync Microsoft Entra provider objects."))
def microsoft_entra_sync_objects(*args, **kwargs):
    return sync_tasks.sync_objects(*args, **kwargs)


@actor(description=_("Full sync for Microsoft Entra provider."))
def microsoft_entra_sync(provider_pk: int, *args, **kwargs):
    """Run full sync for Microsoft Entra provider"""
    return sync_tasks.sync(provider_pk, microsoft_entra_sync_objects)


@actor(description=_("Sync a direct object (user, group) for Microsoft Entra provider."))
def microsoft_entra_sync_direct(*args, **kwargs):
    return sync_tasks.sync_signal_direct(*args, **kwargs)


@actor(
    description=_("Dispatch syncs for a direct object (user, group) for Microsoft Entra providers.")
)
def microsoft_entra_sync_direct_dispatch(*args, **kwargs):
    return sync_tasks.sync_signal_direct_dispatch(microsoft_entra_sync_direct, *args, **kwargs)


@actor(description=_("Sync a related object (memberships) for Microsoft Entra provider."))
def microsoft_entra_sync_m2m(*args, **kwargs):
    return sync_tasks.sync_signal_m2m(*args, **kwargs)


@actor(
    description=_(
        "Dispatch syncs for a related object (memberships) for Microsoft Entra providers."
    )
)
def microsoft_entra_sync_m2m_dispatch(*args, **kwargs):
    return sync_tasks.sync_signal_m2m_dispatch(microsoft_entra_sync_m2m, *args, **kwargs)
