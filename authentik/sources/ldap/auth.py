"""authentik LDAP Authentication Backend"""

from django.http import HttpRequest
from ldap3 import ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, SUBTREE
from ldap3.core.exceptions import LDAPException, LDAPInvalidCredentialsResult
from structlog.stdlib import get_logger

from authentik.core.auth import InbuiltBackend
from authentik.core.models import User
from authentik.sources.ldap.models import LDAP_DISTINGUISHED_NAME, LDAPSource
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from authentik.tasks.middleware import CurrentTask
from authentik.tasks.models import Task

LOGGER = get_logger()


class LDAPBackend(InbuiltBackend):
    """Authenticate users against LDAP Server"""

    def authenticate(self, request: HttpRequest, **kwargs):
        """Try to authenticate a user via ldap"""
        if "password" not in kwargs:
            return None
        for source in LDAPSource.objects.filter(enabled=True):
            LOGGER.debug("LDAP Auth attempt", source=source)
            user = self.auth_user(request, source, **kwargs)
            if user:
                self.set_method("ldap", request, source=source)
                return user
        return None

    def auth_user(
        self, request: HttpRequest, source: LDAPSource, password: str, **filters: str
    ) -> User | None:
        """Try to bind as either user_dn or mail with password.
        Returns True on success, otherwise False"""
        users = User.objects.filter(**filters)
        user: User = None
        if not users.exists():
            if source.sync_just_in_time:
                LOGGER.debug("User not found. Searching for them.")
                sync = UserLDAPSynchronizer(source, Task())
                search_results = sync.search_users(**filters)
                if len(search_results) == 1:
                    LOGGER.debug("Found user and saving them to DB.")
                    user = sync.sync_user(search_results[0])
                    if user == None:
                        LOGGER.debug("Syncing user failed.")
                        return None
                else:
                    LOGGER.debug(f"Searched returned {len(search_results)} results. User not found.")
                    return None
            else:
                return None
        else:
            user = users.first()

        if LDAP_DISTINGUISHED_NAME not in user.attributes:
            LOGGER.debug("User doesn't have DN set, assuming not LDAP imported.", user=user)
            return None
        # Either has unusable password,
        # or has a password, but couldn't be authenticated by ModelBackend.
        # This means we check with a bind to see if the LDAP password has changed
        if self.auth_user_by_bind(source, user, password):
            if source.password_login_update_internal_password:
                # Password given successfully binds to LDAP, so we save it in our Database
                LOGGER.debug("Updating user's password in DB", user=user)
                user.set_password(password, sender=source, request=request)
                user.save()
            return user
        # Password doesn't match
        LOGGER.debug("Failed to bind, password invalid")
        return None

    def auth_user_by_bind(self, source: LDAPSource, user: User, password: str) -> User | None:
        """Attempt authentication by binding to the LDAP server as `user`. This
        method should be avoided as its slow to do the bind."""
        # Try to bind as new user
        LOGGER.debug("Attempting to bind as user", user=user)
        try:
            # source.connection also attempts to bind
            source.connection(
                connection_kwargs={
                    "user": user.attributes.get(LDAP_DISTINGUISHED_NAME),
                    "password": password,
                }
            )
            return user
        except LDAPInvalidCredentialsResult as exc:
            LOGGER.debug("invalid LDAP credentials", user=user, exc=exc)
        except LDAPException as exc:
            LOGGER.warning("failed to bind to LDAP", exc=exc)
        return None
