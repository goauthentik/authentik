"""SCIM provider signals"""

from authentik.common.sync.outgoing.signals import register_signals
from authentik.providers.scim.models import SCIMProvider
from authentik.providers.scim.tasks import scim_sync, scim_sync_direct, scim_sync_m2m

register_signals(
    SCIMProvider,
    task_sync_single=scim_sync,
    task_sync_direct=scim_sync_direct,
    task_sync_m2m=scim_sync_m2m,
)
