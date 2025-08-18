"""Brand utilities"""

from typing import Any

from django.db.models import F
from django.db.models import Value as V
from django.db.models.functions import Length
from django.http.request import HttpRequest
from django.utils.html import _json_script_escapes
from django.utils.safestring import mark_safe

from authentik import authentik_full_version
from authentik.brands.models import Brand
from authentik.lib.sentry import get_http_meta
from authentik.tenants.models import Tenant

DEFAULT_BRAND = Brand(domain="fallback")


def get_brand_for_request(request: HttpRequest) -> Brand:
    """Get brand object for current request"""
    # annotations = {
    #     "host_domain": V(request.get_host()),
    #     "match_length": Length("domain"),
    # }
    # brand = (
    #     Brand.objects.annotate(**annotations)
    #     .filter(host_domain__iendswith=F("domain"))
    #     .order_by("-match_length")
    #     .first()
    # )
    # if not brand:
    #     brand = Brand.objects.filter(default=True).first()
    # if not brand:
    #     return DEFAULT_BRAND
    # return brand
    annotations = {
        "host_domain": V(request.get_host()),
        "match_length": Length("domain"),
    }
    matching_brands = (
        Brand.objects.annotate(**annotations)
        .filter(host_domain__iendswith=F("domain"))
        .order_by("-match_length")
    )
    default_brand = Brand.objects.annotate(**annotations).filter(default=True)
    brand = matching_brands.union(default_brand).first()
    if not brand:
        return DEFAULT_BRAND
    return brand


def context_processor(request: HttpRequest) -> dict[str, Any]:
    """Context Processor that injects brand object into every template"""
    brand = getattr(request, "brand", DEFAULT_BRAND)
    tenant = getattr(request, "tenant", Tenant())
    # similarly to `json_script` we escape everything HTML-related, however django
    # only directly exposes this as a function that also wraps it in a <script> tag
    # which we dont want for CSS
    brand_css = mark_safe(str(brand.branding_custom_css).translate(_json_script_escapes))  # nosec
    return {
        "brand": brand,
        "brand_css": brand_css,
        "footer_links": tenant.footer_links,
        "html_meta": {**get_http_meta()},
        "version": authentik_full_version(),
    }
