"""Helpers for the user-switching browser token cookie."""

from datetime import timedelta

from django.http.request import HttpRequest
from jwt import PyJWTError, decode, encode

from authentik.lib.generators import generate_id
from authentik.lib.utils.crypto import get_cookie_signing_key

TOKEN_LENGTH = 32
# Keep these in sync with web/src/components/ak-user-switcher-storage.ts.
COOKIE_NAME = "authentik_user_switching"
COOKIE_AGE = int(timedelta(days=365).total_seconds())

_SIGNING_HASH = get_cookie_signing_key()


def generate_token() -> str:
    """Generate a new opaque user switching token."""
    return generate_id(TOKEN_LENGTH)


def validate_token(token: str | None) -> str | None:
    """Return the token if it is a well-formed opaque token, else None."""
    if not token:
        return None
    if len(token) != TOKEN_LENGTH:
        return None
    if not token.isalnum():
        return None
    return token


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
