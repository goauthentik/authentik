"""Tenant utils"""
from django.db import connection

from authentik.tenants.models import Tenant


def get_current_tenant() -> Tenant | None:
    """Get tenant for current request"""
    return Tenant.objects.filter(schema_name=connection.schema_name).first()
