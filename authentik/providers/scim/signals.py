"""SCIM provider signals"""

from authentik.lib.sync.outgoing.signals import register_signals
from authentik.providers.scim.models import SCIMProvider
from authentik.providers.scim.tasks import scim_sync_direct_dispatch, scim_sync_m2m_dispatch

register_signals(
    SCIMProvider,
    task_sync_direct_dispatch=scim_sync_direct_dispatch,
    task_sync_m2m_dispatch=scim_sync_m2m_dispatch,
)
