"""Inject brand into current request"""

from collections.abc import Callable

from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils.translation import activate

from authentik.brands.utils import get_brand_for_request


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
        response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Credentials"] = "true"
        if request.method == "OPTIONS":
            response.status_code = 200
            response["Access-Control-Allow-Headers"] = (
                "authorization,sentry-trace,x-authentik-csrf,content-type"
            )
            response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response
