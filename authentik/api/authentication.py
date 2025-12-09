"""API Authentication"""

from hmac import compare_digest
from pathlib import Path
from tempfile import gettempdir
from typing import Any

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.core.middleware import CTX_AUTH_VIA
from authentik.core.models import Token, TokenIntents, User, UserTypes
from authentik.outposts.models import Outpost
from authentik.providers.oauth2.constants import SCOPE_AUTHENTIK_API

LOGGER = get_logger()
_tmp = Path(gettempdir())
try:
    with open(_tmp / "authentik-core-ipc.key") as _f:
        ipc_key = _f.read()
except OSError:
    ipc_key = None


def validate_auth(header: bytes, format="bearer") -> str | None:
    """Validate that the header is in a correct format,
    returns type and credentials"""
    auth_credentials = header.decode().strip()
    if auth_credentials == "" or " " not in auth_credentials:
        return None
    auth_type, _, auth_credentials = auth_credentials.partition(" ")
    if not compare_digest(auth_type.lower(), format):
        LOGGER.debug("Unsupported authentication type, denying", type=auth_type.lower())
        return None
    if auth_credentials == "":  # nosec # noqa
        raise AuthenticationFailed("Malformed header")
    return auth_credentials


class IPCUser(AnonymousUser):
    """'Virtual' user for IPC communication between authentik core and the authentik router"""

    username = "authentik:system"
    is_active = True
    is_superuser = True

    @property
    def type(self):
        return UserTypes.INTERNAL_SERVICE_ACCOUNT

    def has_perm(self, perm, obj=None):
        return True

    def has_perms(self, perm_list, obj=None):
        return True

    def has_module_perms(self, module):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True


class TokenAuthentication(BaseAuthentication):
    """Token-based authentication using HTTP Bearer authentication"""

    def authenticate(self, request: Request) -> tuple[User, Any] | None:
        """Token-based authentication using HTTP Bearer authentication"""
        auth = get_authorization_header(request)

        user_ctx = self.bearer_auth(auth)
        # None is only returned when the header isn't set.
        if not user_ctx:
            return None

        return user_ctx

    def bearer_auth(self, raw_header: bytes) -> tuple[User, Any] | None:
        """raw_header in the Format of `Bearer ....`"""
        user_ctx = self.auth_user_lookup(raw_header)
        if not user_ctx:
            return None
        user, ctx = user_ctx
        if not user.is_active:
            raise AuthenticationFailed("Token invalid/expired")
        return user, ctx

    def auth_user_lookup(self, raw_header: bytes) -> tuple[User, Any] | None:
        """raw_header in the Format of `Bearer ....`"""
        from authentik.providers.oauth2.models import AccessToken

        auth_credentials = validate_auth(raw_header)
        if not auth_credentials:
            return None
        # first, check traditional tokens
        key_token = Token.filter_not_expired(
            key=auth_credentials, intent=TokenIntents.INTENT_API
        ).first()
        if key_token:
            CTX_AUTH_VIA.set("api_token")
            return key_token.user, key_token
        # then try to auth via JWT
        jwt_token = AccessToken.filter_not_expired(
            token=auth_credentials, _scope__icontains=SCOPE_AUTHENTIK_API
        ).first()
        if jwt_token:
            # Double-check scopes, since they are saved in a single string
            # we want to check the parsed version too
            if SCOPE_AUTHENTIK_API not in jwt_token.scope:
                raise AuthenticationFailed("Token invalid/expired")
            CTX_AUTH_VIA.set("jwt")
            return jwt_token.user, jwt_token
        # then try to auth via secret key (for embedded outpost/etc)
        user_outpost = self.token_secret_key(auth_credentials)
        if user_outpost:
            CTX_AUTH_VIA.set("secret_key")
            return user_outpost
        # then try to auth via secret key (for embedded outpost/etc)
        user = self.token_ipc(auth_credentials)
        if user:
            CTX_AUTH_VIA.set("ipc")
            return user
        raise AuthenticationFailed("Token invalid/expired")

    def token_ipc(self, value: str) -> tuple[User, None] | None:
        """Check if the token is the secret key
        and return the service account for the managed outpost"""
        if not ipc_key or not compare_digest(value, ipc_key):
            return None
        return IPCUser(), None

    def token_secret_key(self, value: str) -> tuple[User, Outpost] | None:
        """Check if the token is the secret key
        and return the service account for the managed outpost"""
        from authentik.outposts.apps import MANAGED_OUTPOST

        if not compare_digest(value, settings.SECRET_KEY):
            return None
        outposts = Outpost.objects.filter(managed=MANAGED_OUTPOST)
        if not outposts:
            return None
        outpost = outposts.first()
        return outpost.user, outpost


class TokenSchema(OpenApiAuthenticationExtension):
    """Auth schema"""

    target_class = TokenAuthentication
    name = "authentik"

    def get_security_definition(self, auto_schema):
        """Auth schema"""
        return {"type": "http", "scheme": "bearer"}
