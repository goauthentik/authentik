"""passbook LDAP Authentication Backend"""
from logging import getLogger

from django.contrib.auth.backends import ModelBackend

from passbook.ldap.ldap_connector import LDAPConnector

LOGGER = getLogger(__name__)


class LDAPBackend(ModelBackend):
    """Authenticate users against LDAP Server"""

    def authenticate(self, **kwargs):
        """Try to authenticate a user via ldap"""
        if 'password' not in kwargs:
            return None
        if not LDAPConnector.enabled:
            return None
        _ldap = LDAPConnector()
        return _ldap.auth_user(**kwargs)
