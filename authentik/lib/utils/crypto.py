"""Cryptographic helpers."""

from hashlib import sha512

from django.conf import settings


def get_cookie_signing_key() -> str:
    """Return the shared signing key for authentik's JWT-backed cookies."""
    return sha512(settings.SECRET_KEY.encode()).hexdigest()
