"""Credential backfills preserve references when run again."""

from importlib import import_module

from django.apps import apps
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase
from guardian.models import RoleObjectPermission

from authentik.core.tests.utils import create_test_user
from authentik.crypto.secrets.migrations._credential_values import migrate_credentials
from authentik.crypto.secrets.models import Secret, SecretType
from authentik.providers.oauth2.models import OAuth2Provider


class TestCredentialBackfill(TestCase):
    def test_existing_reference_is_not_replaced(self):
        provider = OAuth2Provider.objects.create(name="existing", client_secret="legacy")
        original = provider.client_secret_ref
        original.replace_value("current")
        count = Secret.objects.count()
        with connection.schema_editor(atomic=False) as editor:
            migrate_credentials(
                apps,
                editor,
                "authentik_providers_oauth2",
                "OAuth2Provider",
                [("client_secret", "client_secret_ref", "text", "client secret")],
                include_empty=True,
            )
        provider.refresh_from_db()
        self.assertEqual(provider.client_secret_ref_id, original.pk)
        self.assertEqual(provider.client_secret_ref.value, "current")
        self.assertEqual(Secret.objects.count(), count)

    def test_scalar_type_does_not_depend_on_newlines(self):
        provider = OAuth2Provider.objects.create(name="scalar", client_secret="legacy\nvalue")
        OAuth2Provider.objects.filter(pk=provider.pk).update(client_secret_ref=None)
        with connection.schema_editor(atomic=False) as editor:
            migrate_credentials(
                apps,
                editor,
                "authentik_providers_oauth2",
                "OAuth2Provider",
                [("client_secret", "client_secret_ref", None, "client secret")],
            )
        provider.refresh_from_db()
        self.assertEqual(provider.client_secret_ref.type, SecretType.TEXT)
        self.assertEqual(provider.client_secret_ref.value, "legacy\nvalue")


class TestProviderPermissionBackfill(TestCase):
    def test_consumer_editors_do_not_gain_secret_write_permissions(self):
        migration = import_module(
            "authentik.crypto.secrets.migrations.0002_preserve_role_permissions"
        )
        provider = OAuth2Provider.objects.create(name="provider")
        other = OAuth2Provider.objects.create(name="other")
        reader = create_test_user()
        editor = create_test_user()
        global_editor = create_test_user()
        reader.assign_perms_to_managed_role(
            "authentik_providers_oauth2.view_oauth2provider", provider
        )
        editor.assign_perms_to_managed_role(
            "authentik_providers_oauth2.change_oauth2provider", provider
        )
        global_editor.assign_perms_to_managed_role(
            "authentik_providers_oauth2.change_oauth2provider"
        )
        historical_apps = MigrationLoader(connection).project_state().apps
        migration.preserve_provider_permissions(historical_apps, connection.schema_editor())
        count = RoleObjectPermission.objects.count()
        migration.preserve_provider_permissions(historical_apps, connection.schema_editor())
        self.assertEqual(RoleObjectPermission.objects.count(), count)
        for user in [reader, editor, global_editor]:
            with self.subTest(user=user):
                secret = provider.client_secret_ref
                self.assertTrue(user.has_perm("authentik_crypto_secrets.view_secret", secret))
                self.assertEqual(
                    user.has_perm("authentik_crypto_secrets.view_secret_value", secret),
                    user != reader,
                )
                for permission in ["change_secret", "rotate_secret"]:
                    self.assertFalse(
                        user.has_perm(f"authentik_crypto_secrets.{permission}", secret)
                    )
                    self.assertFalse(user.has_perm(f"authentik_crypto_secrets.{permission}"))
                self.assertEqual(
                    user.has_perm("authentik_crypto_secrets.view_secret", other.client_secret_ref),
                    user == global_editor,
                )
