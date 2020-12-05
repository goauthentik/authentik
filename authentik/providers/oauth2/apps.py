"""authentik auth oauth provider app config"""
from django.apps import AppConfig


class AuthentikProviderOAuth2Config(AppConfig):
    """authentik auth oauth provider app config"""

    name = "authentik.providers.oauth2"
    label = "authentik_providers_oauth2"
    verbose_name = "authentik Providers.OAuth2"
    mountpoints = {
        "authentik.providers.oauth2.urls": "application/o/",
        "authentik.providers.oauth2.urls_github": "",
    }
