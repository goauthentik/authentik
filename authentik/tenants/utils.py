"""Tenant utilities"""
from django.db.models import Q
from django.http.request import HttpRequest

from authentik.tenants.models import Tenant

_q_default = Q(default=True)


def get_tenant_for_request(request: HttpRequest) -> Tenant:
    """Get tenant object for current request"""
    db_tenants = Tenant.objects.filter(
        Q(domain__iendswith=request.get_host()) | _q_default
    )
    if not db_tenants.exists():
        return Tenant()
    return db_tenants.first()
