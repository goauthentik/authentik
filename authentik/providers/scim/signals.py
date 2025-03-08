"""SCIM provider signals"""

from authentik.lib.sync.outgoing.signals import register_signals
from authentik.providers.scim.models import SCIMProvider

register_signals(
    SCIMProvider,
    task_sync_single="authentik.providers.scim.tasks.scim_sync",
    task_sync_direct="authentik.providers.scim.tasks.scim_sync_direct",
    task_sync_m2m="authentik.providers.scim.tasks.scim_sync_m2m",
)
