"""saml sp helpers"""
from django.http import HttpRequest
from django.shortcuts import reverse

from passbook.channels.in_saml.models import SAMLInlet


def get_issuer(request: HttpRequest, inlet: SAMLInlet) -> str:
    """Get Inlet's Issuer, falling back to our Metadata URL if none is set"""
    issuer = inlet.issuer
    if issuer is None:
        return build_full_url("metadata", request, inlet)
    return issuer


def build_full_url(view: str, request: HttpRequest, inlet: SAMLInlet) -> str:
    """Build Full ACS URL to be used in IDP"""
    return request.build_absolute_uri(
        reverse(f"passbook_channels_in_saml:{view}", kwargs={"inlet_slug": inlet.slug})
    )
