"""Tenant utils"""

from django.db import connection

from authentik.tenants.models import Tenant


def get_current_tenant() -> Tenant | None:
    """Get tenant for current request"""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM information_schema.tables where table_name = 'authentik_tenants_tenant';"
        )
        if not cursor.rowcount:
            return None
    return Tenant.objects.filter(schema_name=connection.schema_name).first()
