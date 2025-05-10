"""Test Settings API"""

from django.urls import reverse

from authentik.core.tests.utils import create_test_admin_user
from authentik.crypto.generators import generate_id
from authentik.tenants.models import Domain, Tenant
from authentik.tenants.tests.utils import TenantAPITestCase

TENANTS_API_KEY = generate_id()
HEADERS = {"Authorization": f"Bearer {TENANTS_API_KEY}"}


class TestSettingsAPI(TenantAPITestCase):
    """Test settings API"""

    def setUp(self):
        super().setUp()
        self.tenant_1 = Tenant.objects.create(
            name=generate_id(), schema_name="t_" + generate_id().lower()
        )
        Domain.objects.create(tenant=self.tenant_1, domain="tenant1.testserver")
        with self.tenant_1:
            self.admin_1 = create_test_admin_user()
        self.tenant_2 = Tenant.objects.create(
            name=generate_id(), schema_name="t_" + generate_id().lower()
        )
        Domain.objects.create(tenant=self.tenant_2, domain="tenant2.testserver")
        with self.tenant_2:
            self.admin_2 = create_test_admin_user()

    def test_settings(self):
        """Test settings API"""
        # First edit settings to different values in two different tenants
        # We need those context managers here because the test client doesn't put itself
        # in the tenant context as a real request would.
        with self.tenant_1:
            self.client.force_login(self.admin_1)
        response = self.client.patch(
            reverse("authentik_api:tenant_settings"),
            data={
                "avatars": "tenant_1_mode",
            },
            HTTP_HOST="tenant1.testserver",
        )
        self.assertEqual(response.status_code, 200)
        with self.tenant_1:
            self.client.logout()

        with self.tenant_2:
            self.client.force_login(self.admin_2)
        response = self.client.patch(
            reverse("authentik_api:tenant_settings"),
            data={
                "avatars": "tenant_2_mode",
            },
            HTTP_HOST="tenant2.testserver",
        )
        self.assertEqual(response.status_code, 200)
        with self.tenant_2:
            self.client.logout()

        # Assert that the settings have changed and are different
        self.tenant_1.refresh_from_db()
        self.tenant_2.refresh_from_db()
        self.assertEqual(self.tenant_1.avatars, "tenant_1_mode")
        self.assertEqual(self.tenant_2.avatars, "tenant_2_mode")
