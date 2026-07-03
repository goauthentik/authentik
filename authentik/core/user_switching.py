"""User switching token.

An opaque, per-browser identifier that groups the logins a browser can switch
between. Unlike the session cookie, it survives individual logins and logouts.

This module is the single owner of the token: generation, validation, signed-cookie
(de)serialization, and the per-request lazy creation shared by the session middleware
and the login path. Keeping it here avoids an ``authentik.core.models`` <->
``authentik.root.middleware`` import cycle.
"""

from datetime import timedelta
from hashlib import sha512

from django.conf import settings
from django.http.request import HttpRequest
from django.utils.crypto import get_random_string
from jwt import PyJWTError, decode, encode

COOKIE_NAME = "authentik_user_switching"
TOKEN_LENGTH = 32
COOKIE_AGE = int(timedelta(days=365).total_seconds())

# Mirrors the session-signing hash in authentik.root.middleware; kept local so this
# module has no dependency on the middleware it is imported by.
_SIGNING_HASH = sha512(settings.SECRET_KEY.encode()).hexdigest()


def generate_token() -> str:
    """Generate a new opaque user switching token."""
    return get_random_string(TOKEN_LENGTH)


def validate_token(raw: str | None) -> str | None:
    """Return the token if it is a well-formed opaque token, else None."""
    if raw and len(raw) == TOKEN_LENGTH and raw.isalnum():
        return raw
    return None


def encode_cookie(token: str) -> str:
    """Encode the opaque token as a signed cookie value."""
    return encode(
        {
            "iss": "authentik",
            "sub": "user_switching",
            "user_switching": token,
        },
        _SIGNING_HASH,
    )


def decode_cookie(raw: str | None) -> str | None:
    """Decode and validate the signed user switching cookie."""
    if not raw:
        return None
    try:
        payload = decode(raw, _SIGNING_HASH, algorithms=["HS256"])
    except PyJWTError:
        return None
    return validate_token(payload.get("user_switching"))


def ensure_request_token(request: HttpRequest) -> str | None:
    """Return the request's user switching token, creating one if the session
    middleware initialized the request but no token is present yet."""
    if not hasattr(request, "user_switching_token"):
        return None
    if not request.user_switching_token:
        request.user_switching_token = generate_token()
        request.user_switching_token_needs_update = True
    return request.user_switching_token
