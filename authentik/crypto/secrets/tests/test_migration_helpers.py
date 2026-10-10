"""Credential backfills preserve references when run again."""

from django.apps import apps
from django.contrib.auth.models import Permission
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.writer import MigrationWriter
from django.db.models import NOT_PROVIDED
from django.test import SimpleTestCase, TestCase
from guardian.models import RoleObjectPermission

from authentik.core.tests.utils import create_test_user
from authentik.crypto.secrets.migrations._credential_values import migrate_credentials
from authentik.crypto.secrets.migrations._permissions import preserve_permissions
from authentik.crypto.secrets.models import Secret
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.rbac.models import InitialPermissions, Role


class TestCredentialMigrationSchema(SimpleTestCase):
    def test_existing_columns_are_unchanged(self):
        """Adding references must preserve the column definitions used by older servers."""
        loader = MigrationLoader(None)
        for node in loader.graph.nodes:
            if not node[1].endswith("_managed_secrets"):
                continue
            before = loader.project_state([node], at_end=False)
            after = loader.project_state([node])
            for key, model in before.models.items():
                if key[0] != node[0]:
                    continue
                for name, field in model.fields.items():
                    with self.subTest(migration=node, model=key, field=name):
                        self.assertIn(name, after.models[key].fields)
                        previous, current = field.clone(), after.models[key].fields[name].clone()
                        # Python defaults can change when the API stops accepting legacy inputs.
                        previous.default = current.default = NOT_PROVIDED
                        self.assertEqual(
                            MigrationWriter.serialize(previous)[0],
                            MigrationWriter.serialize(current)[0],
                        )


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
        self.assertEqual(provider.client_secret_ref.secret_value, "current")
        self.assertEqual(Secret.objects.count(), count)


class TestProviderPermissionBackfill(TestCase):
    def test_consumer_editors_do_not_gain_secret_write_permissions(self):
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
        initial = InitialPermissions.objects.create(
            name="creators", role=Role.objects.create(name="creators")
        )
        initial.permissions.add(Permission.objects.get(codename="change_oauth2provider"))
        historical_apps = MigrationLoader(connection).project_state().apps
        for _ in range(2):
            preserve_permissions(
                historical_apps,
                connection.schema_editor(),
                "authentik_providers_oauth2",
                "oauth2provider",
                value_permission="change",
            )
        count = RoleObjectPermission.objects.count()
        preserve_permissions(
            historical_apps,
            connection.schema_editor(),
            "authentik_providers_oauth2",
            "oauth2provider",
            value_permission="change",
        )
        self.assertEqual(RoleObjectPermission.objects.count(), count)
        self.assertCountEqual(
            initial.permissions.filter(
                content_type__app_label="authentik_crypto_secrets"
            ).values_list("codename", flat=True),
            ["view_secret", "view_secret_value"],
        )
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
