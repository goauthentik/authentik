"""Tenant utils"""
from django.db import connection
from django.db.utils import ProgrammingError

from authentik.tenants.models import Tenant


def get_current_tenant() -> Tenant | None:
    """Get tenant for current request"""
    try:
        return Tenant.objects.filter(schema_name=connection.schema_name).first()
    except ProgrammingError:  # We're inside a migration and this table doesn't exist yet
        return None
