"""SCIM provider signals"""

from authentik.lib.sync.outgoing.signals import register_signals
from authentik.providers.scim.models import SCIMProvider
from authentik.providers.scim.tasks import scim_sync

register_signals(SCIMProvider, task_sync_single=scim_sync)
