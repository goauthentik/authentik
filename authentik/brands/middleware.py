"""Inject brand into current request"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils.translation import activate

from authentik.brands.utils import get_brand_for_request
from authentik.lib.config import CONFIG

if TYPE_CHECKING:
    from authentik.brands.models import Brand


class BrandMiddleware:
    """Add current brand to http request"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not hasattr(request, "brand"):
            brand = get_brand_for_request(request)
            request.brand = brand
            locale = brand.default_locale
            if locale != "":
                activate(locale)
        return self.get_response(request)


class BrandHeaderMiddleware:
    """Add headers from currently active brand"""

    get_response: Callable[[HttpRequest], HttpResponse]
    default_csp_elements: dict[str, list[str]] = {}

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        self.default_csp_elements = {
            "style-src": ["'self'", "'unsafe-inline'"],  # Required due to Lit/ShadowDOM
            "script-src": ["'self'", "'unsafe-inline'"],  # Required for generated scripts
            "img-src": ["https:", "http:", "data:"],
            "default-src": ["'self'"],
            "object-src": ["'none'"],
            "connect-src": ["'self'"],
        }
        if CONFIG.get_bool("error_reporting.enabled"):
            self.default_csp_elements["connect-src"].append(
                # Required for sentry (TODO: Dynamic)
                "https://authentik.error-reporting.a7k.io"
            )
            if CONFIG.get_bool("debug"):
                # Also allow spotlight sidecar connection
                self.default_csp_elements["connect-src"].append("http://localhost:8969")

    def get_csp(self, request: HttpRequest) -> str:
        brand: "Brand" = request.brand
        elements = self.default_csp_elements.copy()
        if brand.origin != "":
            elements["frame-ancestors"] = [brand.origin]
        return ";".join(f"{attr} {" ".join(value)}" for attr, value in elements.items())

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        response.headers["Content-Security-Policy"] = self.get_csp(request)
        return response
