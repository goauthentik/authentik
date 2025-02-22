"""Inject brand into current request"""

from collections.abc import Callable

from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils.translation import override

from authentik.brands.utils import get_brand_for_request


class BrandMiddleware:
    """Add current brand to http request"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        locale_to_set = None
        if not hasattr(request, "brand"):
            brand = get_brand_for_request(request)
            request.brand = brand
            locale = brand.default_locale
            if locale != "":
                locale_to_set = locale
        if locale_to_set:
            with override(locale_to_set):
                return self.get_response(request)
        return self.get_response(request)
