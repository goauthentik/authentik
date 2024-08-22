"""API Authentication"""

from hmac import compare_digest
from typing import Any

from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.api.authentication import validate_auth
from authentik.core.middleware import CTX_AUTH_VIA
from authentik.core.models import User
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.models import Outpost

LOGGER = get_logger()


def bearer_auth(raw_header: bytes) -> User | None:
    """raw_header in the Format of `Bearer ....`"""
    user = auth_user_lookup(raw_header)
    if not user:
        return None
    if not user.is_active:
        raise AuthenticationFailed("Token invalid/expired")
    return user


def auth_user_lookup(raw_header: bytes) -> User | None:
    """raw_header in the Format of `Bearer ....`"""

    auth_credentials = validate_auth(raw_header)
    if not auth_credentials:
        return None
    # then try to auth via secret key (for embedded outpost/etc)
    user = token_secret_key(auth_credentials)
    if user:
        CTX_AUTH_VIA.set("secret_key")
        return user
    return None


def token_secret_key(value: str) -> User | None:
    """Check if the token is the secret key
    and return the service account for the managed outpost"""

    if not compare_digest(value, settings.SECRET_KEY):
        return None
    outposts = Outpost.objects.filter(managed=MANAGED_OUTPOST)
    if not outposts:
        return None
    outpost = outposts.first()
    return outpost.user


class OutpostTokenAuthentication(BaseAuthentication):
    """Token-based authentication using HTTP Bearer authentication"""

    def authenticate(self, request: Request) -> tuple[User, Any] | None:
        """Token-based authentication using HTTP Bearer authentication"""
        auth = get_authorization_header(request)

        user = bearer_auth(auth)
        # None is only returned when the header isn't set.
        if not user:
            return None

        return (user, None)  # pragma: no cover


class OutpostTokenSchema(OpenApiAuthenticationExtension):
    """Auth schema"""

    target_class = OutpostTokenAuthentication
    name = "authentik Outpost"

    def get_security_definition(self, auto_schema):
        """Auth schema"""
        return {"type": "http", "scheme": "bearer"}
