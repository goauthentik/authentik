"""Brand utilities"""

from typing import Any

from django.db.models import Case, F, IntegerField, Q, Value, When
from django.db.models.functions import Length
from django.http.request import HttpRequest
from django.utils.html import _json_script_escapes
from django.utils.safestring import mark_safe

from authentik import authentik_full_version
from authentik.brands.models import Brand
from authentik.lib.sentry import get_http_meta
from authentik.tenants.models import Tenant

_q_default = Q(default=True)
DEFAULT_BRAND = Brand(domain="fallback")


def get_brand_for_request(request: HttpRequest) -> Brand:
    """Get brand object for current request"""

    brand = (
        Brand.objects.annotate(
            host_domain=Value(request.get_host()),
            domain_length=Length("domain"),
            match_priority=Case(
                When(
                    condition=Q(host_domain__iendswith=F("domain")),
                    then=F("domain_length"),
                ),
                default=Value(-1),
                output_field=IntegerField(),
            ),
            is_default_fallback=Case(
                When(
                    condition=Q(default=True),
                    then=Value(0),
                ),
                default=Value(-2),
                output_field=IntegerField(),
            ),
        )
        .filter(Q(match_priority__gt=-1) | Q(default=True))
        .order_by("-match_priority", "-is_default_fallback")
        .first()
    )

    if brand is None:
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
