"""Passbook ldap app config"""

from django.apps import AppConfig


class PassbookInletLDAPConfig(AppConfig):
    """Passbook ldap app config"""

    name = "passbook.channels.in_ldap"
    label = "passbook_channels_in_ldap"
    verbose_name = "passbook Inlets.LDAP"
