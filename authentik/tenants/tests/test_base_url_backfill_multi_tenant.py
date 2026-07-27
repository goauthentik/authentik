"""Tests that the base_url backfill targets the tenant whose schema it runs in"""

from django.apps import apps
from django_tenants.utils import get_public_schema_name, schema_context

from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id
from authentik.tenants.models import Tenant
from authentik.tenants.tests.utils import TenantAPITestCase
from authentik.tenants.utils import get_current_tenant


class TestBaseURLBackfillMultiTenant(TenantAPITestCase):
    """The backfill writes to the running tenant's row, not the public tenant's"""

    @CONFIG.patch("tenants.enabled", True)
    def test_backfill_targets_running_tenant(self):
        """A reconcile run inside a non-public tenant's schema backfills only that tenant"""
        app = apps.get_app_config("authentik_tenants")
        public = get_current_tenant()
        with schema_context(get_public_schema_name()):
            Tenant.objects.filter(pk=public.pk).update(base_url="")

        second = Tenant.objects.create(
            schema_name="t_" + generate_id(length=20).lower(), name="second", ready=True
        )
        with schema_context(get_public_schema_name()):
            Tenant.objects.filter(pk=second.pk).update(base_url="")

        # Run the reconcile only within the second tenant's schema.
        with CONFIG.patch("web.base_url", "https://second.example.com"), second:
            app.backfill_base_url()

        public.refresh_from_db()
        second.refresh_from_db()
        # Persist went to `second` (whose schema the reconcile ran in), not public.
        self.assertEqual(second.base_url, "https://second.example.com")
        self.assertEqual(public.base_url, "")
