"""Tenant utils"""

from urllib.parse import urljoin

from django.db import connection
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


def apply_base_url(url: str) -> str:
    """Make a relative URL absolute by resolving it against the current tenant's configured
    base URL. Absolute URLs, and any URL when no base URL is configured, are returned
    unchanged. Expects server-relative URLs as emitted by `reverse()`, which already carry
    the `web.path` prefix all of authentik's URLs are mounted under."""
    if not url:
        return url
    base_url = get_current_tenant(only=["base_url"]).base_url
    return urljoin(base_url, url)
