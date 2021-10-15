"""webauthn utils"""

from django.http import HttpRequest
from webauthn.helpers.bytes_to_base64url import bytes_to_base64url


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


def bytes_to_base64url_dict(orig: dict) -> dict:
    """The WebAuthn v1 Library does this when decoding the objects to json,
    but since we don't use that (we return a dict instead). Normally the json-serializing
    is done later, but this is a specific conversion that we don't want to apply to all json
    objects"""
    for key, value in orig.items():
        if isinstance(value, bytes):
            orig[key] = bytes_to_base64url(value)
        if isinstance(value, dict):
            orig[key] = bytes_to_base64url_dict(value)
    return orig
