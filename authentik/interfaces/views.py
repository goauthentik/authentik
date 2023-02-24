"""Interface views"""
from json import dumps
from typing import Any, Optional
from urllib.parse import urlencode

from django.http import Http404, HttpRequest, HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect
from django.template import Template, TemplateSyntaxError, engines
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.request import Request

from authentik import get_build_hash
from authentik.admin.tasks import LOCAL_VERSION
from authentik.api.v3.config import ConfigView
from authentik.flows.models import Flow
from authentik.interfaces.models import Interface, InterfaceType
from authentik.lib.utils.urls import reverse_with_qs
from authentik.tenants.api import CurrentTenantSerializer
from authentik.tenants.models import Tenant


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


def redirect_to_default_interface(request: HttpRequest, interface_type: InterfaceType, **kwargs):
    """Shortcut to inline redirect to default interface,
    keeping GET parameters of the passed request"""
    return RedirectToInterface.as_view(type=interface_type)(request, **kwargs)


def reverse_interface(
    request: HttpRequest, interface_type: InterfaceType, query: Optional[QueryDict] = None, **kwargs
):
    """Reverse URL to configured default interface"""
    tenant: Tenant = request.tenant
    interface: Interface = None

    if interface_type == InterfaceType.USER:
        interface = tenant.interface_user
    if interface_type == InterfaceType.ADMIN:
        interface = tenant.interface_admin
    if interface_type == InterfaceType.FLOW:
        interface = tenant.interface_flow

    if not interface:
        raise Http404()
    kwargs["if_name"] = interface.url_name
    return reverse_with_qs(
        "authentik_interfaces:if",
        query=query or request.GET,
        kwargs=kwargs,
    )


class RedirectToInterface(View):
    """Redirect to tenant's configured view for specified type"""

    type: Optional[InterfaceType] = None

    def dispatch(self, request: HttpRequest, **kwargs: Any) -> HttpResponse:
        target = reverse_interface(request, self.type, **kwargs)
        if self.request.GET:
            target += "?" + urlencode(self.request.GET.items())
        return redirect(target)


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
