from django.db.models import Value
from django_tenants.middleware import TenantMainMiddleware
from django_tenants.utils import get_public_schema_name

from authentik.tenants.models import Domain, Tenant


class DefaultTenantMiddleware(TenantMainMiddleware):
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
