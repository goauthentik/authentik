"""authentik SCIM Provider app config"""

from django.apps import AppConfig


class AuthentikProviderSCIMConfig(AppConfig):
    """authentik SCIM Provider app config"""

    name = "authentik.providers.scim"
    label = "authentik_providers_scim"
    verbose_name = "authentik Providers.SCIM"
