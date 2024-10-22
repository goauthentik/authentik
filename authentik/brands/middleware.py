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
        return self.get_response(request)


class BrandCORSAPIMiddleware:
    """CORS for API requests depending on Brand"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def set_headers(self, request: HttpRequest, response: HttpResponse):
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Credentials"] = "true"

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method == "OPTIONS":
            response = HttpResponse(
                status=200,
            )
            self.set_headers(request, response)
            response["Access-Control-Allow-Headers"] = (
                "authorization,sentry-trace,x-authentik-csrf,content-type"
            )
            response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            return response
        response = self.get_response(request)
        self.set_headers(request, response)
        return response
