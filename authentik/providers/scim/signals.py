"""SCIM provider signals"""

from authentik.lib.sync.outgoing.signals import register_signals
from authentik.providers.scim.models import SCIMProvider

register_signals(SCIMProvider)
