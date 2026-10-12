"""webauthn utils"""

from base64 import urlsafe_b64decode, urlsafe_b64encode
from re import fullmatch
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _


def validate_webauthn_origin(value: str) -> None:
    """Validate an exact HTTPS origin or Android signing-certificate origin."""
    android_prefix = "android:apk-key-hash:"
    if value.startswith(android_prefix):
        fingerprint = value[len(android_prefix) :]
        if fullmatch(r"[A-Za-z0-9_-]{43}", fingerprint):
            decoded = urlsafe_b64decode(fingerprint + "=")
            if urlsafe_b64encode(decoded).decode().rstrip("=") == fingerprint:
                return
        raise ValidationError(_("Enter an Android origin with an unpadded base64url SHA-256 hash."))

    URLValidator(schemes=["https"])(value)
    origin = urlsplit(value)
    try:
        # URLValidator checks the port's syntax, but not its range.
        port = origin.port
    except ValueError as exc:
        raise ValidationError(_("Enter an HTTPS origin with a valid port.")) from exc
    if (
        origin.scheme != "https"
        or (port is None and origin.netloc.endswith(":"))
        or origin.username is not None
        or origin.password is not None
        or origin.path
        or "?" in value
        or "#" in value
        or "*" in value
    ):
        raise ValidationError(
            _("Enter an HTTPS origin without a path, query, fragment, or credentials.")
        )


def get_rp_id(request: HttpRequest) -> str:
    """Get hostname from http request, without port"""
    host = request.get_host()
    if ":" in host:
        return host.split(":")[0]
    return host


def get_origin(request: HttpRequest) -> str:
    """Return Origin by building an absolute URL and removing the
    trailing slash"""
    full_url = request.build_absolute_uri("/")
    return full_url[:-1]


def get_expected_origins(request: HttpRequest, additional_origins: list[str]) -> list[str]:
    """Retain the request origin and add explicitly trusted ceremony origins."""
    return list(dict.fromkeys([get_origin(request), *additional_origins]))
