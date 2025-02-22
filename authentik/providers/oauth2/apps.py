"""authentik oauth provider app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikProviderOAuth2Config(ManagedAppConfig):
    """authentik oauth provider app config"""

    name = "authentik.providers.oauth2"
    label = "authentik_providers_oauth2"
    verbose_name = "authentik Providers.OAuth2"
    mountpoints = {
        "authentik.providers.oauth2.urls_root": "",
        "authentik.providers.oauth2.urls": "application/o/",
    }
    default = True
