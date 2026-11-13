"""webauthn utils"""

from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _


def validate_webauthn_origin(value: str) -> None:
    """Reject ambiguous configuration; the WebAuthn library matches origins exactly."""
    if not value or value == "null" or "*" in value or any(char.isspace() for char in value):
        raise ValidationError(
            _(
                "Enter a non-empty origin without whitespace or wildcards. "
                "The value 'null' is not allowed."
            )
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
