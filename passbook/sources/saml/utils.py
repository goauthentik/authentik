"""saml sp helpers"""
from django.http import HttpRequest
from django.shortcuts import reverse

from passbook.sources.saml.models import SAMLSource


def get_issuer(request: HttpRequest, source: SAMLSource) -> str:
    """Get Source's Issuer, falling back to our Metadata URL if none is set"""
    issuer = source.issuer
    if issuer is None:
        return build_full_url("metadata", request, source)
    return issuer


def build_full_url(view: str, request: HttpRequest, source: SAMLSource) -> str:
    """Build Full ACS URL to be used in IDP"""
    return request.build_absolute_uri(
        reverse(f"passbook_sources_saml:{view}", kwargs={"source_slug": source.slug})
    )
