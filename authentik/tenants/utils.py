"""Tenant utilities"""
from typing import Any

from django.db.models import Q
from django.http.request import HttpRequest

from authentik import __version__
from authentik.lib.config import CONFIG
from authentik.tenants.models import Tenant

_q_default = Q(default=True)


def get_tenant_for_request(request: HttpRequest) -> Tenant:
    """Get tenant object for current request"""
    db_tenants = Tenant.objects.filter(
        Q(domain__iendswith=request.get_host()) | _q_default
    )
    if not db_tenants.exists():
        return Tenant(domain="fallback")
    return db_tenants.first()


def context_processor(request: HttpRequest) -> dict[str, Any]:
    """Context Processor that injects tenant object into every template"""
    return {
        "tenant": request.tenant,
        "ak_version": __version__,
        "footer_links": CONFIG.y("authentik.footer_links"),
    }
