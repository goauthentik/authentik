"""Brand utilities"""

from typing import Any

from django.db.models import F, Q
from django.db.models import Value as V
from django.db.models.functions import Length
from django.http.request import HttpRequest
from django.utils.html import _json_script_escapes
from django.utils.safestring import mark_safe

from authentik import get_full_version
from authentik.brands.models import Brand
from authentik.lib.sentry import get_http_meta
from authentik.tenants.models import Tenant

_q_default = Q(default=True)
DEFAULT_BRAND = Brand(domain="fallback")


def get_brand_for_request(request: HttpRequest) -> Brand:
    """Get brand object for current request"""
    db_brands = (
        Brand.objects.annotate(host_domain=V(request.get_host()), match_length=Length("domain"))
        .filter(Q(host_domain__iendswith=F("domain")) | _q_default)
        .order_by("-match_length", "default")
    )
    brands = list(db_brands.all())
    if len(brands) < 1:
        return DEFAULT_BRAND
    return brands[0]


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
        "version": get_full_version(),
    }
