"""webauthn utils"""

from django.http import HttpRequest


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
