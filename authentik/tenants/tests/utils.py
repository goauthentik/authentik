from django.core.management import call_command
from django.db import connection, connections
from rest_framework.test import APITransactionTestCase


class TenantAPITestCase(APITransactionTestCase):
    # Overridden to also remove additional schemas we may have created
    def _fixture_teardown(self):
        super()._fixture_teardown()
        for db_name in self._databases_names(include_mirrors=False):
            with connections[db_name].cursor() as cursor:
                cursor.execute(
                    "SELECT nspname FROM pg_catalog.pg_namespace WHERE nspname !~ 'pg_*' AND nspname != 'information_schema' AND nspname != 'public' AND nspname != 'template'"
                )
                schemas = cursor.fetchall()
                for row in schemas:
                    schema = row[0]
                    cursor.execute(f"DROP SCHEMA {schema} CASCADE")

    def setUp(self):
        call_command("migrate_schemas", schema="template", tenant=True)

    def assertSchemaExists(self, schema_name):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM information_schema.schemata WHERE schema_name = %(schema_name)s",  # nosec
                {"schema_name": schema_name},
            )
            self.assertEqual(cursor.rowcount, 1)

            cursor.execute(
                "SELECT * FROM information_schema.tables WHERE table_schema = 'template'"
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
