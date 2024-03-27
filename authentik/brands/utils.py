"""Brand utilities"""

from typing import Any
from urllib.parse import urlparse

from django.db.models import F, Q
from django.db.models import Value as V
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.utils.cache import patch_vary_headers
from sentry_sdk.hub import Hub
from structlog.stdlib import get_logger

from authentik import get_full_version
from authentik.brands.models import Brand
from authentik.tenants.models import Tenant

_q_default = Q(default=True)
DEFAULT_BRAND = Brand(domain="fallback")
LOGGER = get_logger()


def get_brand_for_request(request: HttpRequest) -> Brand:
    """Get brand object for current request"""
    query = Q(host_domain__iendswith=F("domain"))
    if "Origin" in request.headers:
        query &= Q(Q(origin=request.headers.get("Origin", "")) | Q(origin=""))
    db_brands = (
        Brand.objects.annotate(host_domain=V(request.get_host()))
        .filter(Q(query) | _q_default)
        .order_by("default")
    )
    brands = list(db_brands.all())
    if len(brands) < 1:
        return DEFAULT_BRAND
    return brands[0]


def context_processor(request: HttpRequest) -> dict[str, Any]:
    """Context Processor that injects brand object into every template"""
    brand = getattr(request, "brand", DEFAULT_BRAND)
    tenant = getattr(request, "tenant", Tenant())
    trace = ""
    span = Hub.current.scope.span
    if span:
        trace = span.to_traceparent()
    return {
        "brand": brand,
        "footer_links": tenant.footer_links,
        "sentry_trace": trace,
        "version": get_full_version(),
    }


def cors_allow(request: HttpRequest, response: HttpResponse, *allowed_origins: str):
    """Add headers to permit CORS requests from allowed_origins, with or without credentials,
    with any headers."""
    origin = request.META.get("HTTP_ORIGIN")
    if not origin:
        return response

    # OPTIONS requests don't have an authorization header -> hence
    # we can't extract the provider this request is for
    # so for options requests we allow the calling origin without checking
    allowed = request.method == "OPTIONS"
    received_origin = urlparse(origin)
    for allowed_origin in allowed_origins:
        url = urlparse(allowed_origin)
        if (
            received_origin.scheme == url.scheme
            and received_origin.hostname == url.hostname
            and received_origin.port == url.port
        ):
            allowed = True
    if not allowed:
        LOGGER.warning(
            "CORS: Origin is not an allowed origin",
            requested=received_origin,
            allowed=allowed_origins,
        )
        return response

    # From the CORS spec: The string "*" cannot be used for a resource that supports credentials.
    response["Access-Control-Allow-Origin"] = origin
    patch_vary_headers(response, ["Origin"])
    response["Access-Control-Allow-Credentials"] = "true"

    if request.method == "OPTIONS":
        if "HTTP_ACCESS_CONTROL_REQUEST_HEADERS" in request.META:
            response["Access-Control-Allow-Headers"] = request.META[
                "HTTP_ACCESS_CONTROL_REQUEST_HEADERS"
            ]
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

    return response
