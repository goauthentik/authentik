"""Interface views"""

from json import dumps
from typing import Any

from django.http import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.generic.base import RedirectView, TemplateView
from rest_framework.request import Request

from authentik import get_build_hash
from authentik.admin.tasks import LOCAL_VERSION
from authentik.api.v3.config import ConfigView
from authentik.brands.api import CurrentBrandSerializer
from authentik.brands.models import Brand
from authentik.common.config import CONFIG
from authentik.core.models import UserTypes
from authentik.policies.denied import AccessDeniedResponse


class RootRedirectView(RedirectView):
    """Root redirect view, redirect to brand's default application if set"""

    pattern_name = "authentik_core:if-user"
    query_string = True

    def redirect_to_app(self, request: HttpRequest):
        if request.user.is_authenticated and request.user.type == UserTypes.EXTERNAL:
            brand: Brand = request.brand
            if brand.default_application:
                return redirect(
                    "authentik_core:application-launch",
                    application_slug=brand.default_application.slug,
                )
        return None

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if redirect_response := RootRedirectView().redirect_to_app(request):
            return redirect_response
        return super().dispatch(request, *args, **kwargs)


class InterfaceView(TemplateView):
    """Base interface view"""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["config_json"] = dumps(ConfigView(request=Request(self.request)).get_config().data)
        kwargs["brand_json"] = dumps(CurrentBrandSerializer(self.request.brand).data)
        kwargs["version_family"] = f"{LOCAL_VERSION.major}.{LOCAL_VERSION.minor}"
        kwargs["version_subdomain"] = f"version-{LOCAL_VERSION.major}-{LOCAL_VERSION.minor}"
        kwargs["build"] = get_build_hash()
        kwargs["url_kwargs"] = self.kwargs
        kwargs["base_url"] = self.request.build_absolute_uri(CONFIG.get("web.path", "/"))
        kwargs["base_url_rel"] = CONFIG.get("web.path", "/")
        return super().get_context_data(**kwargs)


class BrandDefaultRedirectView(InterfaceView):
    """By default redirect to default app"""

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.user.is_authenticated and request.user.type == UserTypes.EXTERNAL:
            brand: Brand = request.brand
            if brand.default_application:
                return redirect(
                    "authentik_core:application-launch",
                    application_slug=brand.default_application.slug,
                )
            response = AccessDeniedResponse(self.request)
            response.error_message = _("Interface can only be accessed by internal users.")
            return response
        return super().dispatch(request, *args, **kwargs)
