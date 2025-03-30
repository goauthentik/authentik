"""Microsoft provider signals"""

from authentik.common.sync.outgoing.signals import register_signals
from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProvider
from authentik.enterprise.providers.microsoft_entra.tasks import (
    microsoft_entra_sync,
    microsoft_entra_sync_direct,
    microsoft_entra_sync_m2m,
)

register_signals(
    MicrosoftEntraProvider,
    task_sync_single=microsoft_entra_sync,
    task_sync_direct=microsoft_entra_sync_direct,
    task_sync_m2m=microsoft_entra_sync_m2m,
)
