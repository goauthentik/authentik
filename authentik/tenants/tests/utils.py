from django.core.management import call_command
from django.db import connection, connections
from django_tenants.utils import get_public_schema_name, get_tenant_base_schema, schema_context
from rest_framework.test import APITransactionTestCase

from authentik.tenants.models import Tenant


class TenantAPITestCase(APITransactionTestCase):
    # Overridden to also remove additional schemas we may have created
    def _fixture_teardown(self):
        for db_name in self._databases_names(include_mirrors=False):
            connections[db_name].set_schema_to_public()
            with connections[db_name].cursor() as cursor:
                cursor.execute("SELECT nspname FROM pg_catalog.pg_namespace WHERE nspname ~ 't_.*'")
                schemas = cursor.fetchall()
                for row in schemas:
                    schema = row[0]
                    cursor.execute(f"DROP SCHEMA {schema} CASCADE")
        super()._fixture_teardown()

    def setUp(self):
        with schema_context(get_public_schema_name()):
            Tenant.objects.update_or_create(
                defaults={"name": "Template", "ready": False},
                schema_name=get_tenant_base_schema(),
            )
        call_command("migrate_schemas", schema=get_tenant_base_schema(), tenant=True)

    def assertSchemaExists(self, schema_name):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM information_schema.schemata WHERE schema_name = %(schema_name)s",  # nosec
                {"schema_name": schema_name},
            )
            self.assertEqual(cursor.rowcount, 1)

            cursor.execute(
                "SELECT * FROM information_schema.tables WHERE table_schema = %(schema_name)s",
                {"schema_name": get_tenant_base_schema()},
            )
            expected_tables = cursor.rowcount
            cursor.execute(
                "SELECT * FROM information_schema.tables WHERE table_schema = %(schema_name)s",  # nosec
                {"schema_name": schema_name},
            )
            self.assertEqual(cursor.rowcount, expected_tables)

    def assertSchemaDoesntExist(self, schema_name):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM information_schema.schemata WHERE schema_name = %(schema_name)s",  # nosec
                {"schema_name": schema_name},
            )
            self.assertEqual(cursor.rowcount, 0)
