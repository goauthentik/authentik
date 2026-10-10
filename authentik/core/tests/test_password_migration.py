"""Existing passwords move to password devices."""

from datetime import timedelta
from importlib import import_module

from django.contrib.auth.hashers import make_password
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase
from django.utils.timezone import now

from authentik.core.models import User
from authentik.lib.generators import generate_id
from authentik.stages.password.models import PasswordDevice

MIGRATION = ("authentik_stages_password", "0011_password_devices")


class TestPasswordMigration(TestCase):
    """Run the data copy against the historical models and the retained columns."""

    def test_create_password_devices(self):
        usable, unusable, empty = (User.objects.create(username=generate_id()) for _ in range(3))
        password = make_password(generate_id())
        changed_at = now() - timedelta(days=3)
        with connection.cursor() as cursor:
            # Before the migration, every user row has a password.
            cursor.execute("UPDATE authentik_core_user SET password = '' WHERE password IS NULL")
            cursor.executemany(
                "UPDATE authentik_core_user SET password = %s, password_change_date = %s "
                "WHERE id = %s",
                [
                    (password, changed_at, usable.pk),
                    (make_password(None), changed_at, unusable.pk),
                    ("", changed_at, empty.pk),
                ],
            )
        apps = MigrationLoader(connection).project_state(MIGRATION).apps
        migration = import_module(f"authentik.stages.password.migrations.{MIGRATION[1]}")

        with connection.schema_editor() as schema_editor:
            migration.create_password_devices(apps, schema_editor)

        device = PasswordDevice.objects.get(user=usable)
        self.assertEqual(device.password, password)
        self.assertEqual(device.password_change_date, changed_at)
        self.assertEqual(device.failed_attempts, 0)
        self.assertIsNone(device.locked_at)
        self.assertFalse(PasswordDevice.objects.filter(user__in=[unusable, empty]).exists())
