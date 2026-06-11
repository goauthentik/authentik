"""Tests for seed_database management command."""

from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from authentik.core.management.seed_database import SEED_ATTRIBUTE
from authentik.core.models import Application, ApplicationEntitlement, Group, User
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import OAuth2Provider


class TestSeedDatabaseCommand(TestCase):
    """Test seed_database management command."""

    def test_requires_risk_acknowledgement(self):
        """Test that the command requires explicit acknowledgement."""
        with self.assertRaises(CommandError) as ctx:
            call_command("seed_database")

        self.assertIn("--ack-risk", str(ctx.exception))

    @override_settings(DEBUG=False, TEST=False)
    def test_requires_debug_or_test_mode(self):
        """Test that the command refuses non-development settings."""
        with self.assertRaises(CommandError) as ctx:
            call_command("seed_database", ack_risk=True)

        self.assertIn("DEBUG or TEST", str(ctx.exception))

    @override_settings(DEBUG=False, TEST=True)
    def test_seeds_users_groups_and_memberships(self):
        """Test that users, groups, and memberships are created."""
        out = StringIO()

        call_command(
            "seed_database",
            ack_risk=True,
            prefix="seed-test",
            users=4,
            groups=3,
            superuser_groups=1,
            memberships_per_user=2,
            apps=2,
            entitlements_per_app=2,
            app_group_bindings_per_app=1,
            stdout=out,
        )

        users = User.objects.filter(username__startswith="seed-test-user-").order_by("username")
        groups = Group.objects.filter(name__startswith="seed-test-group-").order_by("name")
        providers = OAuth2Provider.objects.filter(name__startswith="seed-test-provider-")
        apps = Application.objects.filter(slug__startswith="seed-test-app-").order_by("slug")
        entitlements = ApplicationEntitlement.objects.filter(app__in=apps)

        self.assertEqual(users.count(), 4)
        self.assertEqual(groups.count(), 3)
        self.assertEqual(groups.filter(is_superuser=True).count(), 1)
        self.assertEqual(User.groups.through.objects.filter(user__in=users).count(), 8)
        self.assertEqual(providers.count(), 2)
        self.assertEqual(apps.count(), 2)
        self.assertTrue(all(app.provider for app in apps))
        self.assertEqual(entitlements.count(), 4)
        self.assertEqual(
            PolicyBinding.objects.filter(target__in=[*apps, *entitlements]).count(),
            6,
        )
        self.assertTrue(all(user.attributes[SEED_ATTRIBUTE]["mode"] == "static" for user in users))
        self.assertIn("Seeding |", out.getvalue())
        self.assertIn("7/7 policy bindings", out.getvalue())
        self.assertIn(
            "Ensured 4 users, 3 groups, 8 memberships, 2 providers, "
            "2 applications, 4 entitlements, and 6 policy bindings.",
            out.getvalue(),
        )

    @override_settings(DEBUG=False, TEST=True)
    def test_static_mode_is_idempotent(self):
        """Test that static seed data can be rerun without duplicates."""
        options = {
            "ack_risk": True,
            "prefix": "seed-idempotent",
            "users": 3,
            "groups": 2,
            "superuser_groups": 1,
            "memberships_per_user": 1,
            "apps": 2,
            "entitlements_per_app": 1,
            "app_group_bindings_per_app": 1,
        }

        call_command("seed_database", **options)
        call_command("seed_database", **options)

        users = User.objects.filter(username__startswith="seed-idempotent-user-")
        groups = Group.objects.filter(name__startswith="seed-idempotent-group-")
        providers = OAuth2Provider.objects.filter(name__startswith="seed-idempotent-provider-")
        apps = Application.objects.filter(slug__startswith="seed-idempotent-app-")
        entitlements = ApplicationEntitlement.objects.filter(app__in=apps)

        self.assertEqual(users.count(), 3)
        self.assertEqual(groups.count(), 2)
        self.assertEqual(User.groups.through.objects.filter(user__in=users).count(), 3)
        self.assertEqual(providers.count(), 2)
        self.assertEqual(apps.count(), 2)
        self.assertEqual(entitlements.count(), 2)
        self.assertEqual(
            PolicyBinding.objects.filter(target__in=[*apps, *entitlements]).count(),
            4,
        )
