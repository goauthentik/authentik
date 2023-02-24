"""Tenant utilities"""
from typing import Any

from django.db.models import F, Q
from django.db.models import Value as V
from django.http.request import HttpRequest
from rest_framework.request import Request
from sentry_sdk.hub import Hub

from authentik import get_full_version
from authentik.interfaces.models import Interface, InterfaceType
from authentik.lib.config import CONFIG
from authentik.tenants.models import Tenant

_q_default = Q(default=True)


def get_fallback_tenant():
    """Get fallback tenant"""

    fallback_interface = Interface(
        url_name="fallback",
        type=InterfaceType.FLOW,
        template="Fallback interface",
    )
    return Tenant(
        domain="fallback",
        interface_flow=fallback_interface,
        interface_user=fallback_interface,
        interface_admin=fallback_interface,
    )


def get_tenant(request: HttpRequest | Request) -> "Tenant":
    """Get the request's tenant, falls back to a fallback tenant object"""
    if isinstance(request, Request):
        request = request._request
    return getattr(request, "tenant", get_fallback_tenant())


def lookup_tenant_for_request(request: HttpRequest) -> "Tenant":
    """Get tenant object for current request"""
    from authentik.tenants.models import Tenant

    db_tenants = (
        Tenant.objects.annotate(host_domain=V(request.get_host()))
        .filter(Q(host_domain__iendswith=F("domain")) | _q_default)
        .order_by("default")
    )
    tenants = list(db_tenants.all())
    if len(tenants) < 1:
        return get_fallback_tenant()
    return tenants[0]


def context_processor(request: HttpRequest) -> dict[str, Any]:
    """Context Processor that injects tenant object into every template"""
    tenant = getattr(request, "tenant", get_fallback_tenant())
    trace = ""
    span = Hub.current.scope.span
    if span:
        trace = span.to_traceparent()
    return {
        "tenant": tenant,
        "footer_links": CONFIG.y("footer_links"),
        "sentry_trace": trace,
        "version": get_full_version(),
    }
