"""Authentik SCIM app config"""

from django.apps import AppConfig


class AuthentikSourceSCIMConfig(AppConfig):
    """authentik SCIM Source app config"""

    name = "authentik.sources.scim"
    label = "authentik_sources_scim"
    verbose_name = "authentik Sources.SCIM"
