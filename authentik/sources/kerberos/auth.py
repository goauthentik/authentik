"""authentik Kerberos Authentication Backend"""

import gssapi
from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.core.auth import InbuiltBackend
from authentik.core.models import User
from authentik.lib.generators import generate_id
from authentik.sources.kerberos.models import (
    KerberosSource,
    Krb5ConfContext,
    UserKerberosSourceConnection,
)

LOGGER = get_logger()


class KerberosBackend(InbuiltBackend):
    """Authenticate users against Kerberos realm"""

    def authenticate(self, request: HttpRequest, **kwargs):
        """Try to authenticate a user via kerberos"""
        if "password" not in kwargs or "username" not in kwargs:
            return None
        username = kwargs.pop("username")
        realm = None
        if "@" in username:
            username, realm = username.rsplit("@", 1)

        user, source = self.auth_user(username, realm, **kwargs)
        if user:
            self.set_method("kerberos", request, source=source)
            return user
        return None

    def auth_user(
        self, username: str, realm: str | None, password: str, **filters
    ) -> tuple[User | None, KerberosSource | None]:
        sources = KerberosSource.objects.filter(enabled=True)
        user = User.objects.filter(
            usersourceconnection__source__in=sources, username=username, **filters
        ).first()

        if user is not None:
            # User found, let's get its connections for the sources that are available
            user_source_connections = UserKerberosSourceConnection.objects.filter(
                user=user, source__in=sources
            )
        elif realm is not None:
            user_source_connections = UserKerberosSourceConnection.objects.filter(
                source__in=sources, identifier=f"{username}@{realm}"
            )
        # no realm specified, we can't do anything
        else:
            user_source_connections = UserKerberosSourceConnection.objects.none()

        if not user_source_connections.exists():
            LOGGER.debug("no kerberos source found for user", username=username)
            return None, None

        for user_source_connection in user_source_connections.prefetch_related().select_related(
            "source__kerberossource"
        ):
            # User either has an unusable password,
            # or has a password, but couldn't be authenticated by ModelBackend
            # This means we check with a kinit to see if the Kerberos password has changed
            if self.auth_user_by_kinit(user_source_connection, password):
                # Password was successful in kinit to Kerberos, so we save it in database
                if (
                    user_source_connection.source.kerberossource.password_login_update_internal_password
                ):
                    LOGGER.debug(
                        "Updating user's password in DB",
                        source=user_source_connection.source,
                        user=user_source_connection.user,
                    )
                    user_source_connection.user.set_password(
                        password, sender=user_source_connection.source
                    )
                    user_source_connection.user.save()
                return user_source_connection.user, user_source_connection.source
            # Password doesn't match, onto next source
            LOGGER.debug(
                "failed to kinit, password invalid",
                source=user_source_connection.source,
                user=user_source_connection.user,
            )
        # No source with valid password found
        LOGGER.debug("no valid kerberos source found for user", user=user)
        return None, None

    def auth_user_by_kinit(
        self, user_source_connection: UserKerberosSourceConnection, password: str
    ) -> bool:
        """Attempt authentication by kinit to the source."""
        LOGGER.debug(
            "Attempting to kinit as user",
            user=user_source_connection.user,
            source=user_source_connection.source,
            principal=user_source_connection.identifier,
        )

        with Krb5ConfContext(user_source_connection.source.kerberossource):
            name = gssapi.raw.import_name(
                user_source_connection.identifier.encode(), gssapi.raw.NameType.kerberos_principal
            )
            try:
                # Use a temporary credentials cache to not interfere with whatever is defined
                # elsewhere
                gssapi.raw.ext_krb5.krb5_ccache_name(f"MEMORY:{generate_id(12)}".encode())
                gssapi.raw.ext_password.acquire_cred_with_password(name, password.encode())
                # Restore the credentials cache to what it was before
                gssapi.raw.ext_krb5.krb5_ccache_name(None)
                return True
            except gssapi.exceptions.GSSError as exc:
                LOGGER.warning("failed to kinit", exc=exc)
        return False
