"""authentik LDAP Authentication Backend"""
from typing import Optional

import ldap3
from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.sources.ldap.models import LDAPSource

LOGGER = get_logger()
LDAP_DISTINGUISHED_NAME = "distinguishedName"


class LDAPBackend(ModelBackend):
    """Authenticate users against LDAP Server"""

    def authenticate(self, request: HttpRequest, **kwargs):
        """Try to authenticate a user via ldap"""
        if "password" not in kwargs:
            return None
        for source in LDAPSource.objects.filter(enabled=True):
            LOGGER.debug("LDAP Auth attempt", source=source)
            user = self.auth_user(source, **kwargs)
            if user:
                return user
        return None

    def auth_user(self, source: LDAPSource, password: str, **filters: str) -> Optional[User]:
        """Try to bind as either user_dn or mail with password.
        Returns True on success, otherwise False"""
        users = User.objects.filter(**filters)
        if not users.exists():
            return None
        user: User = users.first()
        if LDAP_DISTINGUISHED_NAME not in user.attributes:
            LOGGER.debug("User doesn't have DN set, assuming not LDAP imported.", user=user)
            return None
        # Either has unusable password,
        # or has a password, but couldn't be authenticated by ModelBackend.
        # This means we check with a bind to see if the LDAP password has changed
        if self.auth_user_by_bind(source, user, password):
            # Password given successfully binds to LDAP, so we save it in our Database
            LOGGER.debug("Updating user's password in DB", user=user)
            user.set_password(password, signal=False)
            user.save()
            return user
        # Password doesn't match
        LOGGER.debug("Failed to bind, password invalid")
        return None

    def auth_user_by_bind(self, source: LDAPSource, user: User, password: str) -> Optional[User]:
        """Attempt authentication by binding to the LDAP server as `user`. This
        method should be avoided as its slow to do the bind."""
        # Try to bind as new user
        LOGGER.debug("Attempting Binding as user", user=user)
        try:
            temp_connection = ldap3.Connection(
                source.connection.server,
                user=user.attributes.get(LDAP_DISTINGUISHED_NAME),
                password=password,
                raise_exceptions=True,
            )
            temp_connection.bind()
            return user
        except ldap3.core.exceptions.LDAPInvalidCredentialsResult as exception:
            LOGGER.debug("LDAPInvalidCredentialsResult", user=user, error=exception)
        except ldap3.core.exceptions.LDAPException as exception:
            LOGGER.warning(exception)
        return None
