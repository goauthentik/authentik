"""authentik tenants app"""
from django.db import DEFAULT_DB_ALIAS
from django.db.backends.signals import connection_created
from django.db.models.signals import post_migrate
from django_tenants.utils import get_public_schema_name

from authentik.blueprints.apps import ManagedAppConfig


def ensure_default_tenant(*args, using=DEFAULT_DB_ALIAS, connection=None, **kwargs):
    """Make sure default tenant exists"""
    # Make sure we've migrated before touching the database
    if connection is not None:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'authentik_tenants_tenant'"
            )
            if not bool(cursor.rowcount):
                return
        using = connection.alias

    from django_tenants.utils import schema_context

    from authentik.tenants.models import Tenant

    with schema_context(get_public_schema_name()):
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
        ensure_default_tenant()
        post_migrate.connect(ensure_default_tenant)
        connection_created.connect(ensure_default_tenant)
