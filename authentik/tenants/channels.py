from channels.db import database_sync_to_async
from django.db import close_old_connections, connection
from django.http.request import split_domain_port
from django_tenants.utils import (
    get_public_schema_name,
    remove_www,
)

from authentik.tenants.models import Domain, Tenant


class TenantsAwareMiddleware:
    """Set the database schema for use with django-tenants"""

    def __init__(self, inner):
        self.inner = inner

    def get_hostname_from_scope(self, scope: list[tuple[bytes, bytes]]) -> str | None:
        headers = {k.replace(b"-", b"_").upper(): v for k, v in scope.get("headers", [])}
        hostname, _ = split_domain_port(headers.get(b"HOST", b"").decode("utf-8"))
        if not hostname:
            return None
        return remove_www(hostname)

    async def get_default_tenant(self) -> Tenant:
        return await database_sync_to_async(Tenant.objects.get)(
            schema_name=get_public_schema_name()
        )

    async def get_tenant(self, hostname: str | None) -> Tenant:
        if not hostname:
            return await self.get_default_tenant()

        try:
            domain = await database_sync_to_async(Domain.objects.select_related("tenant").get)(
                domain=hostname
            )
        except Domain.DoesNotExist:
            return await self.get_default_tenant()
        return domain.tenant

    async def __call__(self, scope, receive, send):
        close_old_connections()
        hostname = self.get_hostname_from_scope(scope)
        tenant = await self.get_tenant(hostname)
        scope["tenant"] = tenant
        connection.set_tenant(tenant)
        return await self.inner(scope, receive, send)
