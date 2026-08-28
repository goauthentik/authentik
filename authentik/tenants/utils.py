"""Tenant utils"""

from django.core.exceptions import ValidationError
from django.db import connection
from django.utils.translation import gettext_lazy as _
from django_tenants.utils import get_public_schema_name

from authentik.lib.config import CONFIG
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


def normalize_base_url(value: str | None) -> str:
    """Normalize a configured base URL: strip whitespace and trailing slashes."""
    return (value or "").strip().rstrip("/")


def validate_base_url(value: str) -> None:
    """Validate a base URL: an http or https scheme, followed by something."""
    if not value:
        return
    scheme, separator, rest = value.partition("://")
    if scheme.lower() not in ("http", "https") or not separator or not rest:
        raise ValidationError(_("Enter a valid URL, for example https://authentik.company"))
