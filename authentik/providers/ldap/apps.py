"""authentik ldap provider app config"""

from django.apps import AppConfig


class AuthentikProviderLDAPConfig(AppConfig):
    """authentik ldap provider app config"""

    name = "authentik.providers.ldap"
    label = "authentik_providers_ldap"
    verbose_name = "authentik Providers.LDAP"
