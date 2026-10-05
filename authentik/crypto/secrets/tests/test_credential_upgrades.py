"""Managed credentials preserve their original columns across upgrades and downgrades."""

from base64 import b64encode
from importlib import import_module
from json import loads
from unittest.mock import patch

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from dramatiq import get_broker

from authentik.core.tests.utils import create_test_flow
from authentik.tasks.test import TESTING_QUEUE


class TestCredentialUpgrades(TransactionTestCase):
    @patch("authentik.outposts.signals.outpost_send_update.send_with_options")
    def test_upgrade_preserves_columns_and_downgrade_restores_values(self, _send_update):
        get_broker().join(TESTING_QUEUE, timeout=10_000)
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        migrations = {
            node: migration
            for node, migration in executor.loader.graph.nodes.items()
            if node[1].endswith("_managed_secrets")
        }
        preceding = {
            node[0]: dependency
            for node, migration in migrations.items()
            for dependency in migration.dependencies
            if dependency[0] == node[0]
        }
        before = [preceding.get(node[0], node) for node in latest]
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(latest))
        executor.migrate(before)
        state = executor.loader.project_state(before)
        records = self.create_credentials(state, migrations)

        executor = MigrationExecutor(connection)
        executor.migrate(latest)
        state = executor.loader.project_state(latest)
        for app_label, model_name, pk, fields, values in records:
            obj = state.apps.get_model(app_label, model_name).objects.get(pk=pk)
            with self.subTest(upgrade=model_name, pk=pk):
                for old, new, _, _ in fields:
                    secret = getattr(obj, new)
                    value = loads(secret.value) if isinstance(values[old], dict) else secret.value
                    self.assertEqual(value, values[old])
                    self.assertEqual(getattr(obj, old), values[old])
                    with connection.cursor() as cursor:
                        columns = connection.introspection.get_table_description(
                            cursor, obj._meta.db_table
                        )
                    self.assertIn(old, {column.name for column in columns})
                    replacement = (
                        '{"token": "replacement"}'
                        if isinstance(values[old], dict)
                        else "replacement"
                    )
                    secret.value = replacement
                    # Exercise decoding uploaded structured files during rollback too.
                    if isinstance(values[old], dict):
                        secret.type = "file"
                        secret.value = b64encode(replacement.encode()).decode()
                    secret.save(update_fields=["type", "value"])

        executor = MigrationExecutor(connection)
        executor.migrate(before)
        state = executor.loader.project_state(before)
        for app_label, model_name, pk, fields, values in records:
            obj = state.apps.get_model(app_label, model_name).objects.get(pk=pk)
            with self.subTest(downgrade=model_name, pk=pk):
                for old, _, _, _ in fields:
                    expected = (
                        {"token": "replacement"} if isinstance(values[old], dict) else "replacement"
                    )
                    self.assertEqual(getattr(obj, old), expected)

    def create_credentials(self, state, migrations):
        records = []
        for node, migration in migrations.items():
            module = import_module(migration.__module__)
            models = {op.model_name for op in migration.operations if hasattr(op, "model_name")}
            self.assertEqual(len(models), 1)
            model_name = models.pop()
            Model = state.apps.get_model(node[0], model_name)
            values = {
                old: (
                    {"token": " original "}
                    if Model._meta.get_field(old).get_internal_type() == "JSONField"
                    else " original "
                )
                for old, _, _, _ in module.FIELDS
            }
            kwargs = {"name": model_name, **values}
            if any(field.name == "slug" for field in Model._meta.fields):
                kwargs["slug"] = model_name
            if model_name == "telegramsource":
                kwargs["pre_authentication_flow_id"] = create_test_flow().pk
            obj = Model.objects.create(**kwargs)
            records.append((node[0], model_name, obj.pk, module.FIELDS, values))
            if model_name in {"oauth2provider", "radiusprovider"}:
                empty = {old: "" for old in values}
                obj = Model.objects.create(name=f"{model_name} empty", **empty)
                records.append((node[0], model_name, obj.pk, module.FIELDS, empty))

        return records
