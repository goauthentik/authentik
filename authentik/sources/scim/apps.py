"""Authentik SCIM app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikSourceSCIMConfig(ManagedAppConfig):
    """authentik SCIM Source app config"""

    name = "authentik.sources.scim"
    label = "authentik_sources_scim"
    verbose_name = "authentik Sources.SCIM"
    mountpoint = "source/scim/"
    default = True
