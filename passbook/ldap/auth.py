"""passbook LDAP Authentication Backend"""
from django.contrib.auth.backends import ModelBackend
from structlog import get_logger

from passbook.ldap.ldap_connector import LDAPConnector
from passbook.ldap.models import LDAPSource

LOGGER = get_logger()


class LDAPBackend(ModelBackend):
    """Authenticate users against LDAP Server"""

    def authenticate(self, **kwargs):
        """Try to authenticate a user via ldap"""
        if 'password' not in kwargs:
            return None
        for source in LDAPSource.objects.filter(enabled=True):
            _ldap = LDAPConnector(source)
            user = _ldap.auth_user(**kwargs)
            if user:
                return user
        return None
