from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View

from authentik.brands.models import Brand, WebfingerProvider
from authentik.core.models import Application


class WebFingerView(View):
    """Webfinger endpoint"""

    def get(self, request: HttpRequest) -> HttpResponse:
        brand: Brand = request.brand
        if not brand.default_application:
            return JsonResponse({})
        application: Application = brand.default_application
        provider = application.get_provider()
        if not provider or not isinstance(provider, WebfingerProvider):
            return JsonResponse({})
        webfinger_data = provider.webfinger(request.GET.get("resource"), request)
        return JsonResponse(webfinger_data)

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response = super().dispatch(request, *args, **kwargs)
        # RFC7033 spec
        response["Access-Control-Allow-Origin"] = "*"
        response["Content-Type"] = "application/jrd+json"
        return response
