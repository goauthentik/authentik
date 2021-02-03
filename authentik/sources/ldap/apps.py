"""authentik ldap source config"""
from importlib import import_module

from django.apps import AppConfig


class AuthentikSourceLDAPConfig(AppConfig):
    """Authentik ldap app config"""

    name = "authentik.sources.ldap"
    label = "authentik_sources_ldap"
    verbose_name = "authentik Sources.LDAP"

    def ready(self):
        import_module("authentik.sources.ldap.signals")
        import_module("authentik.sources.ldap.managed")
