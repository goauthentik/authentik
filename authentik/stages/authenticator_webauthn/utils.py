"""webauthn utils"""

from django.http import HttpRequest

from authentik.stages.authenticator_webauthn.models import WebAuthnRPConfig


def get_rp_config(request: HttpRequest) -> WebAuthnRPConfig | None:
    """Get the WebAuthn RP config assigned to the request's brand, if any"""
    brand = getattr(request, "brand", None)
    if not brand:
        return None
    return brand.webauthn_rp_config


def get_rp_id(request: HttpRequest) -> str:
    """Get the WebAuthn RP ID: the RP ID of the brand's WebAuthn RP config if one is
    assigned, otherwise the hostname from the http request, without port"""
    rp_config = get_rp_config(request)
    if rp_config:
        return rp_config.rp_id
    host = request.get_host()
    if ":" in host:
        return host.split(":")[0]
    return host


def get_origin(request: HttpRequest) -> str | list[str]:
    """Get the expected WebAuthn origin(s): the explicit origin list of the brand's
    WebAuthn RP config if one is assigned, otherwise the Origin built from the
    request's absolute URL without the trailing slash"""
    rp_config = get_rp_config(request)
    if rp_config:
        # Deliberately no fallback for an empty list: the RP ID from the config
        # must never be paired with a request-derived origin
        return list(rp_config.origins)
    full_url = request.build_absolute_uri("/")
    return full_url[:-1]
