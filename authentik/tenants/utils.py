from django.db.models import F, Value
from django.http import HttpRequest

from authentik.tenants.models import Tenant, get_default_tenant


def get_tenant_for_request(request: HttpRequest) -> Tenant:
    """Get tenant for current request"""
    tenants = list(
        Tenant.objects.alias(domain=Value(request.get_host()))
        .filter(domain__iregex=F("domain_regex"))
        .all()
    )
    # We always have one match at least for the default tenant
    if len(tenants) <= 1:
        return tenants[0]
    for tenant in tenants:
        if tenant.domain_regex != ".*":
            return tenant
    return get_default_tenant()
