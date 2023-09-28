"""Tenant utilities"""
from typing import Any

from django.db.models import F, Q
from django.db.models import Value as V
from django.http.request import HttpRequest
from sentry_sdk.hub import Hub

from authentik import get_full_version
from authentik.lib.config import CONFIG
from authentik.tenants.models import Tenant

_q_default = Q(default=True)
DEFAULT_TENANT = Tenant(domain="fallback")


def get_tenant_for_request(request: HttpRequest) -> Tenant:
    """Get tenant object for current request"""
    db_tenants = (
        Tenant.objects.annotate(host_domain=V(request.get_host()))
        .filter(Q(host_domain__iendswith=F("domain")) | _q_default)
        .order_by("default")
    )
    tenants = list(db_tenants.all())
    if len(tenants) < 1:
        return DEFAULT_TENANT
    return tenants[0]


def context_processor(request: HttpRequest) -> dict[str, Any]:
    """Context Processor that injects tenant object into every template"""
    tenant = getattr(request, "tenant", DEFAULT_TENANT)
    trace = ""
    span = Hub.current.scope.span
    if span:
        trace = span.to_traceparent()
    return {
        "tenant": tenant,
        "footer_links": CONFIG.get("footer_links"),
        "sentry_trace": trace,
        "version": get_full_version(),
    }
