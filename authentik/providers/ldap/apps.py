"""authentik ldap provider app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikProviderLDAPConfig(ManagedAppConfig):
    """authentik ldap provider app config"""

    name = "authentik.providers.ldap"
    label = "authentik_providers_ldap"
    verbose_name = "authentik Providers.LDAP"
    default = True
