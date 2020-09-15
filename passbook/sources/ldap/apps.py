"""passbook ldap source config"""
from importlib import import_module

from django.apps import AppConfig


class PassbookSourceLDAPConfig(AppConfig):
    """Passbook ldap app config"""

    name = "passbook.sources.ldap"
    label = "passbook_sources_ldap"
    verbose_name = "passbook Sources.LDAP"

    def ready(self):
        import_module("passbook.sources.ldap.signals")
