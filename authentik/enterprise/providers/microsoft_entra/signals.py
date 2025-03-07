"""Microsoft provider signals"""

from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProvider
from authentik.lib.sync.outgoing.signals import register_signals

register_signals(
    MicrosoftEntraProvider,
    task_sync_single="authentik.enterprise.providers.microsoft_entra.tasks.microsoft_entra_sync",
    task_sync_direct="authentik.enterprise.providers.microsoft_entra.tasks.microsoft_entra_sync_direct",
    task_sync_m2m="authentik.enterprise.providers.microsoft_entra.tasks.microsoft_entra_sync_m2m",
)
