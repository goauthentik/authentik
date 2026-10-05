"""Password storage survives upgrades and downgrades."""

from django.contrib.auth.hashers import make_password
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils.timezone import now

from authentik.lib.generators import generate_id


class TestPasswordMigration(TransactionTestCase):
    """Exercise the data copy using historical models and the real migration graph."""

    def test_password_round_trip(self):
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(latest))
        previous = [
            ("authentik_core", "0066_user_authentik_core_user_email_idx"),
            ("authentik_stages_password", "0010_alter_passwordstage_backends"),
        ]
        executor.migrate(previous)
        old_apps = executor.loader.project_state(previous).apps
        users = old_apps.get_model("authentik_core", "User").objects
        password = make_password(generate_id())
        user = users.create(username=generate_id(), password=password)
        changed_at = user.password_change_date

        executor = MigrationExecutor(connection)
        executor.migrate(latest)
        apps = executor.loader.project_state(latest).apps
        devices = apps.get_model("authentik_stages_password", "PasswordDevice").objects
        device = devices.get(user_id=user.pk)
        self.assertEqual(device.password, password)
        self.assertEqual(device.password_change_date, changed_at)
        self.assertEqual(device.failed_attempts, 0)
        self.assertIsNone(device.locked_at)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT password, password_change_date FROM authentik_core_user WHERE id = %s",
                [user.pk],
            )
            self.assertEqual(cursor.fetchone(), (None, None))

        password = make_password(generate_id())
        changed_at = now()
        devices.filter(pk=device.pk).update(password=password, password_change_date=changed_at)
        new_user = apps.get_model("authentik_core", "User").objects.create(username=generate_id())
        devices.create(user=new_user, name="Password", password=password)
        passwordless = apps.get_model("authentik_core", "User").objects.create(
            username=generate_id()
        )

        MigrationExecutor(connection).migrate(previous)
        user = users.get(pk=user.pk)
        self.assertEqual(user.password, password)
        self.assertEqual(user.password_change_date, changed_at)
        self.assertEqual(users.get(pk=new_user.pk).password, password)
        self.assertEqual(users.get(pk=passwordless.pk).password, "!")
