"""authentik tenants app"""
from django.db import DEFAULT_DB_ALIAS
from django.db.models.signals import post_migrate

from authentik.blueprints.apps import ManagedAppConfig


def reconcile_default_tenant(*args, using=DEFAULT_DB_ALIAS, **kwargs):
    """Make sure default tenant exists"""
    from authentik.tenants.models import Tenant

    Tenant.objects.using(using).update_or_create(
        defaults={"name": "Default", "ready": True},
        schema_name="public",
    )


class AuthentikTenantsConfig(ManagedAppConfig):
    """authentik tenants app"""

    name = "authentik.tenants"
    label = "authentik_tenants"
    verbose_name = "authentik Tenants"
    default = True

    def reconcile_default_tenant(self):
        """Make sure default tenant exists, especially after a migration"""
        reconcile_default_tenant()
        post_migrate.connect(reconcile_default_tenant)
