"""Authentik SPNEGO app config"""
from authentik.blueprints.apps import ManagedAppConfig


class AuthentikSourceSPNEGOConfig(ManagedAppConfig):
    """authentik spnego source app config"""

    name = "authentik.sources.spnego"
    label = "authentik_sources_spnego"
    verbose_name = "authentik Sources.SPNEGO"
    mountpoint = "source/spnego/"
    default = True
