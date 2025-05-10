"""Test Tenant API"""

from json import loads

from django.urls import reverse

from authentik.crypto.generators import generate_id
from authentik.lib.config import CONFIG
from authentik.tenants.tests.utils import TenantAPITestCase

TENANTS_API_KEY = generate_id()
HEADERS = {"Authorization": f"Bearer {TENANTS_API_KEY}"}


class TestAPI(TenantAPITestCase):
    """Test api view"""

    @CONFIG.patch("outposts.disable_embedded_outpost", True)
    @CONFIG.patch("tenants.enabled", True)
    @CONFIG.patch("tenants.api_key", TENANTS_API_KEY)
    def test_tenant_create_delete(self):
        """Test Tenant creation API Endpoint"""
        response = self.client.post(
            reverse(
                "authentik_api:tenant-list",
            ),
            data={"name": generate_id(), "schema_name": "t_" + generate_id(length=63 - 2).lower()},
            headers=HEADERS,
        )
        self.assertEqual(response.status_code, 201)
        body = loads(response.content.decode())

        self.assertSchemaExists(body["schema_name"])

        response = self.client.delete(
            reverse(
                "authentik_api:tenant-detail",
                kwargs={"pk": body["tenant_uuid"]},
            ),
            headers=HEADERS,
        )
        self.assertEqual(response.status_code, 204)
        self.assertSchemaDoesntExist(body["schema_name"])

    @CONFIG.patch("outposts.disable_embedded_outpost", True)
    @CONFIG.patch("tenants.enabled", True)
    @CONFIG.patch("tenants.api_key", TENANTS_API_KEY)
    def test_unauthenticated(self):
        """Test Tenant creation API Endpoint"""
        response = self.client.get(
            reverse(
                "authentik_api:tenant-list",
            ),
        )
        self.assertEqual(response.status_code, 403)

    @CONFIG.patch("outposts.disable_embedded_outpost", True)
    @CONFIG.patch("tenants.enabled", True)
    @CONFIG.patch("tenants.api_key", "")
    def test_no_api_key_configured(self):
        """Test Tenant creation API Endpoint"""
        response = self.client.get(
            reverse(
                "authentik_api:tenant-list",
            ),
        )
        self.assertEqual(response.status_code, 403)
