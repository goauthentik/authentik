"""Passbook ldap app config"""

from django.apps import AppConfig


class PassbookSourceLDAPConfig(AppConfig):
    """Passbook ldap app config"""

    name = 'passbook.sources.ldap'
    label = 'passbook_sources_ldap'
    verbose_name = 'passbook Sources.LDAP'
