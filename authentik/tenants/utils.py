"""Tenant utils"""

from django.core.signals import request_started
from django.db import connection
from django_tenants.utils import get_public_schema_name

from authentik.lib.config import CONFIG
from authentik.root.install_id import get_install_id
from authentik.tenants.models import Tenant

# Per-connection memoization for ``get_current_tenant``. Cache lives on the
# Django connection (thread-local); key is ``(schema_name, frozenset(only))``.
# Tenant switches via django_tenants update ``schema_name`` and naturally
# invalidate. The ``only`` argument is part of the key so calls during
# migrations (where the Tenant table may not yet have all columns) stay
# correct — different callers pass different ``only`` sets.
_TENANT_CACHE_ATTR = "_authentik_current_tenant"


def get_current_tenant(only: list[str] | None = None) -> Tenant:
    """Get tenant for current request.

    Memoized per Django connection by ``(schema_name, frozenset(only or []))``.
    With the authentik default ``CONN_MAX_AGE=0`` the connection closes at
    request end, so the cache is effectively per-request. With persistent
    connections, the ``request_started`` signal handler below clears the
    cache at request boundaries as defense-in-depth.
    """
    schema = connection.schema_name
    if only is None:
        only = []
    cache_key = (schema, frozenset(only))

    cached = getattr(connection, _TENANT_CACHE_ATTR, None)
    if cached is not None:
        cached_key, cached_tenant = cached
        if cached_key == cache_key:
            return cached_tenant

    tenant = Tenant.objects.only(*only).get(schema_name=schema)
    setattr(connection, _TENANT_CACHE_ATTR, (cache_key, tenant))
    return tenant


def _clear_current_tenant_cache(sender, **kwargs):
    """Clear the per-connection tenant cache at request boundaries. Ensures
    the cache cannot survive a request even on deployments with persistent
    Django connections (``CONN_MAX_AGE>0``).
    """
    if hasattr(connection, _TENANT_CACHE_ATTR):
        try:
            delattr(connection, _TENANT_CACHE_ATTR)
        except AttributeError:
            pass


request_started.connect(_clear_current_tenant_cache, dispatch_uid="authentik_tenants_utils")


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
