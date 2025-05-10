"""Tenant utils"""

from django.db import connection
from django_tenants.utils import get_public_schema_name

from authentik.common.config import CONFIG
from authentik.root.install_id import get_install_id
from authentik.tenants.models import Tenant


def get_current_tenant(only: list[str] | None = None) -> Tenant:
    """Get tenant for current request"""
    if only is None:
        only = []
    return Tenant.objects.only(*only).get(schema_name=connection.schema_name)


def get_unique_identifier() -> str:
    """Get a globally unique identifier that does not change"""
    install_id = get_install_id()
    if CONFIG.get_bool("tenants.enabled"):
        tenant = get_current_tenant()
        # Only use tenant's uuid if this request is not from the "public"
        # (i.e. default) tenant
        if tenant.schema_name == get_public_schema_name():
            return install_id
        return str(get_current_tenant().tenant_uuid)
    return install_id
