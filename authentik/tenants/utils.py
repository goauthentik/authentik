from django.db import connection

from authentik.tenants.models import Tenant


def get_current_tenant() -> Tenant:
    """Get tenant for current request"""
    return connection.tenant
