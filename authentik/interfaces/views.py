"""Interface views"""
from json import dumps
from typing import Any

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.template import Template, TemplateSyntaxError, engines
from django.template.response import TemplateResponse
from django.views import View
from rest_framework.request import Request
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from authentik import get_build_hash
from authentik.admin.tasks import LOCAL_VERSION
from authentik.api.v3.config import ConfigView
from authentik.flows.models import Flow
from authentik.interfaces.models import Interface, InterfaceType
from authentik.tenants.api import CurrentTenantSerializer


def template_from_string(template_string: str) -> Template:
    """Render template from string"""
    chain = []
    engine_list = engines.all()
    for engine in engine_list:
        try:
            return engine.from_string(template_string)
        except TemplateSyntaxError as exc:
            chain.append(exc)
    raise TemplateSyntaxError(template_string, chain=chain)


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(cache_page(60 * 10), name="dispatch")
class InterfaceView(View):
    """General interface view"""

    def get_context_data(self) -> dict[str, Any]:
        """Get template context"""
        return {
            "config_json": dumps(ConfigView(request=Request(self.request)).get_config().data),
            "tenant_json": dumps(CurrentTenantSerializer(self.request.tenant).data),
            "version_family": f"{LOCAL_VERSION.major}.{LOCAL_VERSION.minor}",
            "version_subdomain": f"version-{LOCAL_VERSION.major}-{LOCAL_VERSION.minor}",
            "build": get_build_hash(),
        }

    def type_flow(self, context: dict[str, Any]):
        """Special handling for flow interfaces"""
        if self.kwargs.get("flow_slug", None) is None:
            raise Http404()
        context["flow"] = get_object_or_404(Flow, slug=self.kwargs.get("flow_slug"))
        context["inspector"] = "inspector" in self.request.GET

    def dispatch(self, request: HttpRequest, if_name: str, **kwargs: Any) -> HttpResponse:
        context = self.get_context_data()
        # TODO: Cache
        interface: Interface = get_object_or_404(Interface, url_name=if_name)
        if interface.type == InterfaceType.FLOW:
            self.type_flow(context)
        template = template_from_string(interface.template)
        return TemplateResponse(request, template, context)
