"""authentik radius provider app config"""
from django.apps import AppConfig


class AuthentikProviderRadiusConfig(AppConfig):
    """authentik radius provider app config"""

    name = "authentik.providers.radius"
    label = "authentik_providers_radius"
    verbose_name = "authentik Providers.Radius"
