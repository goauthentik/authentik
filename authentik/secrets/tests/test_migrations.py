"""Secret data migration tests."""

from importlib import import_module
from json import loads

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase, TransactionTestCase
from dramatiq import get_broker
from guardian.models import RoleModelPermission, RoleObjectPermission

from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.events.models import NotificationTransport
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.rbac.models import Role
from authentik.secrets.models import Secret
from authentik.sources.ldap.models import LDAPSource
from authentik.stages.authenticator_sms.models import AuthenticatorSMSStage
from authentik.tasks.test import TESTING_QUEUE

OLD_MIGRATIONS = [
    ("authentik_secrets", "0001_initial"),
    ("authentik_events", "0020_alter_event_action"),
    ("authentik_providers_oauth2", "0037_accesstoken_actor_authorizationcode_actor_and_more"),
    ("authentik_providers_proxy", "0016_proxysession"),
    ("authentik_providers_radius", "0005_radiusprovider_certificate"),
    ("authentik_providers_scim", "0021_scimprovider_discovery_enabled"),
    ("authentik_sources_ldap", "0012_ldapsource_sync_group_parents"),
    ("authentik_sources_oauth", "0015_oauthsource_url_textfields"),
    ("authentik_sources_plex", "0006_migrate_groupplexsourceconnection"),
    ("authentik_sources_telegram", "0001_initial"),
    ("authentik_stages_authenticator_duo", "0008_alter_duodevice_stage"),
    ("authentik_stages_authenticator_email", "0004_alter_emaildevice_stage"),
    ("authentik_stages_authenticator_sms", "0010_alter_smsdevice_stage"),
    ("authentik_stages_captcha", "0005_captchastage_request_content_type"),
    ("authentik_stages_email", "0006_emailstage_recovery_cache_timeout_and_more"),
    ("authentik_endpoints_connectors_fleet", "0001_initial"),
    ("authentik_providers_microsoft_entra", "0006_microsoftentraprovider_discovery_enabled"),
    ("authentik_providers_google_workspace", "0007_googleworkspaceprovider_discovery_enabled"),
    ("authentik_endpoints_connectors_google_chrome", "0001_initial"),
    (
        "authentik_stages_authenticator_endpoint_gdtc",
        "0002_alter_authenticatorendpointgdtcstage_friendly_name",
    ),
    ("authentik_outposts", "0022_outpostprovider_alter_outpost_providers"),
    ("authentik_sources_kerberos", "0005_alter_kerberossource_kadmin_type"),
    ("guardian", "0005_delete_userobjectpermission_and_groupobjectpermission"),
]

LATEST_MIGRATIONS = [
    ("authentik_secrets", "0002_preserve_role_permissions"),
    ("authentik_events", "0022_remove_notificationtransport__webhook_url"),
    ("authentik_providers_oauth2", "0039_remove_oauth2provider__client_secret"),
    ("authentik_providers_proxy", "0018_remove_proxyprovider__cookie_secret"),
    ("authentik_providers_radius", "0007_remove_radiusprovider__shared_secret"),
    ("authentik_providers_scim", "0023_remove_scimprovider__token"),
    ("authentik_sources_ldap", "0014_remove_ldapsource__bind_password"),
    ("authentik_sources_oauth", "0017_remove_oauthsource__consumer_secret"),
    ("authentik_sources_plex", "0008_remove_plexsource__plex_token"),
    ("authentik_sources_telegram", "0003_remove_telegramsource__bot_token"),
    (
        "authentik_stages_authenticator_duo",
        "0010_remove_authenticatorduostage__admin_secret_key_and_more",
    ),
    ("authentik_stages_authenticator_email", "0006_remove_authenticatoremailstage__password"),
    ("authentik_stages_authenticator_sms", "0012_remove_authenticatorsmsstage__auth_and_more"),
    ("authentik_stages_captcha", "0007_remove_captchastage__private_key"),
    ("authentik_stages_email", "0008_remove_emailstage__password"),
    ("authentik_endpoints_connectors_fleet", "0004_remove_fleetconnector__token"),
    ("authentik_providers_microsoft_entra", "0009_remove_microsoftentraprovider__client_secret"),
    ("authentik_providers_google_workspace", "0009_remove_googleworkspaceprovider_credentials"),
    (
        "authentik_endpoints_connectors_google_chrome",
        "0003_remove_googlechromeconnector_credentials",
    ),
    (
        "authentik_stages_authenticator_endpoint_gdtc",
        "0004_remove_authenticatorendpointgdtcstage_credentials",
    ),
    ("authentik_outposts", "0024_remove_kubernetesserviceconnection_kubeconfig"),
    ("authentik_sources_kerberos", "0008_remove_kerberossource__sync_password_and_more"),
    ("guardian", "0005_delete_userobjectpermission_and_groupobjectpermission"),
]


class TestSecretMigration(TransactionTestCase):
    """Upgrade populated credential columns, then downgrade edited secrets."""

    def test_upgrade_and_downgrade(self):
        get_broker().join(TESTING_QUEUE, timeout=10_000)
        executor = MigrationExecutor(connection)
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(LATEST_MIGRATIONS))
        executor.migrate(OLD_MIGRATIONS)
        state = executor.loader.project_state(OLD_MIGRATIONS)
        consumers = [
            ("authentik_events", "NotificationTransport", {"webhook_url": "secret"}),
            ("authentik_providers_oauth2", "OAuth2Provider", {"client_secret": "secret"}),
            ("authentik_providers_radius", "RadiusProvider", {"shared_secret": "secret"}),
            ("authentik_providers_scim", "SCIMProvider", {"token": "secret"}),
            ("authentik_sources_ldap", "LDAPSource", {"bind_password": "secret"}),
            ("authentik_sources_oauth", "OAuthSource", {"consumer_secret": "secret"}),
            ("authentik_sources_plex", "PlexSource", {"plex_token": "secret"}),
            ("authentik_sources_telegram", "TelegramSource", {"bot_token": "secret"}),
            (
                "authentik_stages_authenticator_duo",
                "AuthenticatorDuoStage",
                {"client_secret": "secret", "admin_secret_key": "admin_secret"},
            ),
            (
                "authentik_stages_authenticator_email",
                "AuthenticatorEmailStage",
                {"password": "secret"},
            ),
            (
                "authentik_stages_authenticator_sms",
                "AuthenticatorSMSStage",
                {"auth": "auth_secret", "auth_password": "auth_password_secret"},
            ),
            ("authentik_stages_captcha", "CaptchaStage", {"private_key": "secret"}),
            ("authentik_stages_email", "EmailStage", {"password": "secret"}),
            ("authentik_endpoints_connectors_fleet", "FleetConnector", {"token": "secret"}),
            (
                "authentik_providers_microsoft_entra",
                "MicrosoftEntraProvider",
                {"client_secret": "secret"},
            ),
            (
                "authentik_providers_google_workspace",
                "GoogleWorkspaceProvider",
                {"credentials": "secret"},
            ),
            (
                "authentik_endpoints_connectors_google_chrome",
                "GoogleChromeConnector",
                {"credentials": "secret"},
            ),
            (
                "authentik_stages_authenticator_endpoint_gdtc",
                "AuthenticatorEndpointGDTCStage",
                {"credentials": "secret"},
            ),
            ("authentik_outposts", "KubernetesServiceConnection", {"kubeconfig": "secret"}),
            (
                "authentik_sources_kerberos",
                "KerberosSource",
                {
                    "sync_password": "secret",
                    "sync_keytab": "sync_keytab_secret",
                    "sync_ccache": "sync_ccache_secret",
                    "spnego_keytab": "spnego_keytab_secret",
                    "spnego_ccache": "spnego_ccache_secret",
                },
            ),
        ]
        role = Role.objects.create(name="credential editor")
        records = []
        for app, model_name, fields in consumers:
            Model = state.apps.get_model(app, model_name)
            values = {
                name: (
                    {"token": " original "}
                    if Model._meta.get_field(name).get_internal_type() == "JSONField"
                    else " original "
                )
                for name in fields
            }
            kwargs = {"name": model_name, **values}
            if any(field.name == "slug" for field in Model._meta.fields):
                kwargs["slug"] = model_name.lower()
            if model_name == "TelegramSource":
                kwargs["pre_authentication_flow_id"] = create_test_flow().pk
            obj = Model.objects.create(**kwargs)
            permission = state.apps.get_model("auth", "Permission").objects.get(
                content_type__app_label=app, codename=f"change_{model_name.lower()}"
            )
            state.apps.get_model("guardian", "RoleObjectPermission").objects.create(
                role_id=role.pk,
                permission=permission,
                content_type_id=permission.content_type_id,
                object_pk=str(obj.pk),
            )
            records.append((app, model_name, obj.pk, fields, values))

        ProxyProvider = state.apps.get_model("authentik_providers_proxy", "ProxyProvider")
        proxy = ProxyProvider.objects.create(name="ProxyProvider", cookie_secret=" original ")
        records.append(
            (
                "authentik_providers_proxy",
                "ProxyProvider",
                proxy.pk,
                {"cookie_secret": "cookie_secret_ref"},
                {"cookie_secret": " original "},
            )
        )

        for app, model_name, field in [
            ("authentik_providers_oauth2", "OAuth2Provider", "client_secret"),
            ("authentik_providers_radius", "RadiusProvider", "shared_secret"),
        ]:
            obj = state.apps.get_model(app, model_name).objects.create(
                name=f"{model_name} empty", **{field: ""}
            )
            records.append((app, model_name, obj.pk, {field: "secret"}, {field: ""}))

        executor = MigrationExecutor(connection)
        executor.migrate(LATEST_MIGRATIONS)
        state = executor.loader.project_state(LATEST_MIGRATIONS)
        for app, model_name, pk, fields, values in records:
            obj = state.apps.get_model(app, model_name).objects.get(pk=pk)
            with self.subTest(model=model_name):
                for old_field, new_field in fields.items():
                    secret = getattr(obj, new_field)
                    value = (
                        loads(secret.value) if isinstance(values[old_field], dict) else secret.value
                    )
                    self.assertEqual(value, values[old_field])
                    self.assertNotIn(old_field, {f.name for f in obj._meta.fields})
                    if values[old_field] and app != "authentik_providers_proxy":
                        self.assertTrue(
                            RoleObjectPermission.objects.filter(
                                role=role,
                                object_pk=str(secret.pk),
                                permission__codename="rotate_secret",
                            ).exists()
                        )
                    secret.value = (
                        '{"token": "replacement"}' if isinstance(value, dict) else "replacement"
                    )
                    secret.save(update_fields=["value"])

        executor = MigrationExecutor(connection)
        executor.migrate(OLD_MIGRATIONS)
        state = executor.loader.project_state(OLD_MIGRATIONS)
        for app, model_name, pk, fields, values in records:
            obj = state.apps.get_model(app, model_name).objects.get(pk=pk)
            with self.subTest(downgrade=model_name):
                for field in fields:
                    expected = (
                        {"token": "replacement"}
                        if isinstance(values[field], dict)
                        else "replacement"
                    )
                    self.assertEqual(getattr(obj, field), expected)


class TestSecretPermissionMigration(TestCase):
    def test_preserve_roles_without_broadening_value_access(self):
        migration = import_module("authentik.secrets.migrations.0002_preserve_role_permissions")
        provider = OAuth2Provider.objects.create(name="provider")
        other_provider = OAuth2Provider.objects.create(name="other provider")
        ldap = LDAPSource.objects.create(
            name="ldap", slug="ldap", secret=Secret.objects.create(name="ldap")
        )
        transport = NotificationTransport.objects.create(
            name="transport", secret=Secret.objects.create(name="webhook")
        )
        sms = AuthenticatorSMSStage.objects.create(
            name="sms",
            auth_secret=Secret.objects.create(name="auth"),
            auth_password_secret=Secret.objects.create(name="password"),
        )
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
        editor.assign_perms_to_managed_role("authentik_sources_ldap.change_ldapsource", ldap)
        reader.assign_perms_to_managed_role(
            "authentik_events.view_notificationtransport", transport
        )
        editor.assign_perms_to_managed_role(
            "authentik_stages_authenticator_sms.change_authenticatorsmsstage", sms
        )
        existing_secret_role = Role.objects.create(name="existing secret role")
        existing_secret_role.assign_perms("authentik_secrets.view_secret")
        apps = MigrationLoader(connection).project_state().apps
        model_permission_count = RoleModelPermission.objects.filter(
            content_type__app_label="authentik_secrets"
        ).count()
        migration.preserve_role_permissions(apps, connection.schema_editor())
        count = RoleObjectPermission.objects.count()
        migration.preserve_role_permissions(apps, connection.schema_editor())
        self.assertEqual(RoleObjectPermission.objects.count(), count)

        self.assertTrue(reader.has_perm("authentik_secrets.view_secret", provider.secret))
        self.assertFalse(reader.has_perm("authentik_secrets.view_secret_value", provider.secret))
        self.assertFalse(reader.has_perm("authentik_secrets.rotate_secret", provider.secret))
        self.assertTrue(editor.has_perm("authentik_secrets.view_secret_value", provider.secret))
        self.assertTrue(editor.has_perm("authentik_secrets.rotate_secret", provider.secret))
        self.assertFalse(editor.has_perm("authentik_secrets.view_secret", other_provider.secret))
        self.assertTrue(
            global_editor.has_perm("authentik_secrets.rotate_secret", other_provider.secret)
        )
        self.assertFalse(global_editor.has_perm("authentik_secrets.rotate_secret"))
        self.assertTrue(reader.has_perm("authentik_secrets.view_secret_value", transport.secret))
        for secret in [ldap.secret, sms.auth_secret, sms.auth_password_secret]:
            self.assertTrue(editor.has_perm("authentik_secrets.change_secret", secret))
            self.assertTrue(editor.has_perm("authentik_secrets.rotate_secret", secret))
            self.assertFalse(editor.has_perm("authentik_secrets.view_secret_value", secret))
        self.assertEqual(
            RoleModelPermission.objects.filter(content_type__app_label="authentik_secrets").count(),
            model_permission_count,
        )

    def test_every_consumer_migrates_grants(self):
        core = import_module("authentik.secrets.migrations.0002_preserve_role_permissions")
        apps = MigrationLoader(connection).project_state().apps
        enterprise = [
            ("authentik_endpoints_connectors_fleet", "fleetconnector"),
            ("authentik_providers_microsoft_entra", "microsoftentraprovider"),
            ("authentik_providers_google_workspace", "googleworkspaceprovider"),
            ("authentik_endpoints_connectors_google_chrome", "googlechromeconnector"),
            ("authentik_stages_authenticator_endpoint_gdtc", "authenticatorendpointgdtcstage"),
            ("authentik_outposts", "kubernetesserviceconnection"),
        ]
        role = Role.objects.create(name="editor")
        for app_label, model_name in core.CONSUMERS + enterprise:
            with self.subTest(model=model_name):
                Model = apps.get_model(app_label, model_name)
                fields = [
                    field.name
                    for field in Model._meta.fields
                    if field.related_model
                    and field.related_model._meta.label_lower == "authentik_secrets.secret"
                ]
                secrets = {
                    name: Secret.objects.create(name=f"{model_name} {name}") for name in fields
                }
                kwargs = (
                    {"slug": model_name}
                    if any(field.name == "slug" for field in Model._meta.fields)
                    else {}
                )
                if model_name == "telegramsource":
                    kwargs["pre_authentication_flow_id"] = create_test_flow().pk
                instance = Model.objects.create(
                    name=model_name,
                    **kwargs,
                    **{f"{name}_id": secret.pk for name, secret in secrets.items()},
                )
                role.assign_perms(f"{app_label}.change_{model_name}", instance)
                core.preserve_role_permissions(
                    apps, connection.schema_editor(), [(app_label, model_name)]
                )
                for secret in secrets.values():
                    self.assertTrue(
                        RoleObjectPermission.objects.filter(
                            role=role,
                            object_pk=str(secret.pk),
                            permission__codename="rotate_secret",
                        ).exists()
                    )
