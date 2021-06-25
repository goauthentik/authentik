"""Tenant utilities"""
from typing import Any

from django.db.models import F, Q
from django.db.models import Value as V
from django.http.request import HttpRequest

from authentik import __version__
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
    if not db_tenants.exists():
        return DEFAULT_TENANT
    return db_tenants.first()


def context_processor(request: HttpRequest) -> dict[str, Any]:
    """Context Processor that injects tenant object into every template"""
    tenant = getattr(request, "tenant", DEFAULT_TENANT)
    return {
        "tenant": tenant,
        "ak_version": __version__,
        "footer_links": CONFIG.y("footer_links"),
    }
