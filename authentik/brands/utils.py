"""Brand utilities"""

from typing import Any

from django.db.models import F, Q
from django.db.models import Value as V
from django.http.request import HttpRequest
from sentry_sdk.hub import Hub

from authentik import get_full_version
from authentik.brands.models import Brand

_q_default = Q(default=True)
DEFAULT_BRAND = Brand(domain="fallback")


def get_brand_for_request(request: HttpRequest) -> Brand:
    """Get brand object for current request"""
    db_brands = (
        Brand.objects.annotate(host_domain=V(request.get_host()))
        .filter(Q(host_domain__iendswith=F("domain")) | _q_default)
        .order_by("default")
    )
    brands = list(db_brands.all())
    if len(brands) < 1:
        return DEFAULT_BRAND
    return brands[0]


def context_processor(request: HttpRequest) -> dict[str, Any]:
    """Context Processor that injects brand object into every template"""
    brand = getattr(request, "brand", DEFAULT_BRAND)
    trace = ""
    span = Hub.current.scope.span
    if span:
        trace = span.to_traceparent()
    return {
        "brand": brand,
        "footer_links": request.tenant.footer_links,
        "sentry_trace": trace,
        "version": get_full_version(),
    }
