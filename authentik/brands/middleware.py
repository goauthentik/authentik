"""Inject brand into current request"""
from typing import Callable

from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils.translation import activate
from sentry_sdk.api import set_tag

from authentik.brands.utils import get_brand_for_request


class BrandMiddleware:
    """Add current brand to http request"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not hasattr(request, "brand"):
            brand = get_brand_for_request(request)
            setattr(request, "brand", brand)
            set_tag("authentik.brand_uuid", brand.brand_uuid.hex)
            set_tag("authentik.brand_domain", brand.domain)
            locale = brand.default_locale
            if locale != "":
                activate(locale)
        return self.get_response(request)
