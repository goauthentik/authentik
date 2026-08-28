from django.db import connection
from django.db.models import Value
from django.http import HttpRequest, HttpResponse
from django_tenants.middleware import TenantMainMiddleware
from django_tenants.utils import get_public_schema_name

from authentik.tenants.models import Domain, Tenant


class DefaultTenantMiddleware(TenantMainMiddleware):
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Skip for liveness probe
        if request.path == "/-/health/live/":
            connection.set_schema_to_public()
            return self.get_response(request)

        return super().__call__(request)

    def get_tenant(self, domain_model: type[Domain], hostname: str) -> Tenant:
        tenant = (
            Tenant.objects.filter(domains__domain=hostname)
            .annotate(default=Value(100))
            .union(
                Tenant.objects.filter(schema_name=get_public_schema_name()).annotate(
                    default=Value(10)
                )
            )
            .order_by("-default")
            .first()
        )
        if tenant is None:
            raise domain_model.DoesNotExist()
        return tenant
