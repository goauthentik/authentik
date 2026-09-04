"""Secret data migration tests."""

from importlib import import_module

from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase


class TestSecretMigration(TestCase):
    """Preserve credential edits when reversing a migration."""

    def test_duo_round_trip(self):
        migration = import_module(
            "authentik.stages.authenticator_duo.migrations.0009_authenticatorduostage_secret"
        )
        apps = MigrationLoader(connection).project_state().apps
        Stage = apps.get_model("authentik_stages_authenticator_duo", "AuthenticatorDuoStage")
        Secret = apps.get_model("authentik_secrets", "Secret")
        existing = Secret.objects.create(name="test Duo client secret", value="other")
        stage = Stage.objects.create(
            name="test", _client_secret=" original ", _admin_secret_key="admin"
        )
        editor = connection.schema_editor()

        migration.migrate_secrets(apps, editor)
        stage.refresh_from_db()
        self.assertEqual(stage.secret.value, " original ")
        self.assertEqual(stage.admin_secret.value, "admin")
        self.assertNotEqual(stage.secret.pk, existing.pk)

        stage.secret.value = "replacement"
        stage.secret.save(update_fields=["value"])
        stage.admin_secret = None
        stage.save(update_fields=["admin_secret"])
        migration.rollback_secrets(apps, editor)

        stage.refresh_from_db()
        self.assertEqual(stage._client_secret, "replacement")
        self.assertEqual(stage._admin_secret_key, "")
