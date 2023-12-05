"""Test Tenant API"""
from json import loads

from django.core.management import call_command
from django.db import connection
from django.urls import reverse
from rest_framework.test import APILiveServerTestCase, APITestCase, APITransactionTestCase

from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id

TENANTS_API_KEY = generate_id()
HEADERS = {"Authorization": f"Bearer {TENANTS_API_KEY}"}


class TestAPI(APITransactionTestCase):
    """Test api view"""

    def _fixture_teardown(self):
        for db_name in self._databases_names(include_mirrors=False):
            call_command(
                "flush",
                verbosity=0,
                interactive=False,
                database=db_name,
                reset_sequences=False,
                allow_cascade=True,
                inhibit_post_migrate=False,
            )

    def setUp(self):
        call_command("migrate_schemas", schema="template", tenant=True)

    def assertSchemaExists(self, schema_name):
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM information_schema.schemata WHERE schema_name = '{schema_name}';"
            )
            self.assertEqual(cursor.rowcount, 1)

            cursor.execute(
                "SELECT * FROM information_schema.tables WHERE table_schema = 'template';"
            )
            expected_tables = cursor.rowcount
            cursor.execute(
                f"SELECT * FROM information_schema.tables WHERE table_schema = '{schema_name}';"
            )
            self.assertEqual(cursor.rowcount, expected_tables)

    def assertSchemaDoesntExist(self, schema_name):
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM information_schema.schemata WHERE schema_name = '{schema_name}';"
            )
            self.assertEqual(cursor.rowcount, 0)

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

    @CONFIG.patch("tenants.enabled", False)
    @CONFIG.patch("tenants.api_key", TENANTS_API_KEY)
    def test_api_disabled(self):
        """Test Tenant creation API Endpoint"""
        response = self.client.get(
            reverse(
                "authentik_api:tenant-list",
            ),
            headers=HEADERS,
        )
        self.assertEqual(response.status_code, 404)
