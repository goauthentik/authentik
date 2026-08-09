"""authentik tenants app"""

from django.db import DEFAULT_DB_ALIAS
from django.db.models.signals import post_migrate
from django_tenants.utils import get_public_schema_name, schema_context

from authentik.blueprints.apps import ManagedAppConfig
from authentik.core.apps import Setup
from authentik.lib.config import CONFIG
from authentik.outposts.apps import MANAGED_OUTPOST

# Deprecation identifier for the configuration warning surfaced when no base URL is configured.
BASE_URL_UNSET_DEPRECATION = "authentik.tenants.base_url_unset"


def ensure_default_tenant(*args, using=DEFAULT_DB_ALIAS, **kwargs):
    """Make sure default tenant exists"""
    from authentik.tenants.models import Tenant

    with schema_context(get_public_schema_name()):
        Tenant.objects.using(using).update_or_create(
            defaults={"name": "Default", "ready": True},
            schema_name=get_public_schema_name(),
        )


class AuthentikTenantsConfig(ManagedAppConfig):
    """authentik tenants app"""

    name = "authentik.tenants"
    label = "authentik_tenants"
    verbose_name = "authentik Tenants"
    default = True

    @ManagedAppConfig.reconcile_global
    def default_tenant(self):
        """Make sure default tenant exists, especially after a migration"""
        post_migrate.connect(ensure_default_tenant)
        ensure_default_tenant()

    @ManagedAppConfig.reconcile_tenant
    def backfill_base_url(self):
        """Backfill base_url when it hasn't been set yet. Sources: AUTHENTIK_WEB__BASE_URL config
        value, then the embedded outpost's configured host. When neither is available, warn that
        the base URL must be set before it becomes required in a future release."""
        from authentik.events.models import Event
        from authentik.outposts.models import Outpost
        from authentik.tenants.models import Tenant
        from authentik.tenants.utils import get_current_tenant, normalize_base_url

        tenant = get_current_tenant()
        if tenant.base_url:
            return  # Already set
        base_url = normalize_base_url(CONFIG.get("web.base_url", ""))
        if not base_url:
            outpost = Outpost.objects.filter(managed=MANAGED_OUTPOST).first()
            if outpost:
                base_url = normalize_base_url(outpost.config.authentik_host)
        if not base_url:  # No source available
            if Setup.get(tenant=tenant):  # Only nag instances that have finished setup
                self.logger.warning("Base URL is not configured", tenant=tenant.schema_name)
                Event.log_deprecation(
                    BASE_URL_UNSET_DEPRECATION,
                    "No base URL is configured. A configured base URL will be required "
                    "in a future release. Set it in the system settings or via the "
                    "AUTHENTIK_WEB__BASE_URL environment variable.",
                    cause=tenant.schema_name,
                )
            return
        with schema_context(get_public_schema_name()):
            Tenant.objects.filter(pk=tenant.pk).update(base_url=base_url)
        self.logger.info("Backfilled base_url", base_url=base_url)
