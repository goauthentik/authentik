"""authentik ldap source config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikSourceLDAPConfig(ManagedAppConfig):
    """Authentik ldap app config"""

    name = "authentik.sources.ldap"
    label = "authentik_sources_ldap"
    verbose_name = "authentik Sources.LDAP"
    default = True
