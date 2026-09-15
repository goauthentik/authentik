from json import loads

from django.db import connections, migrations

from authentik.lib.config import CONFIG

JSON_FIELDS = ("footer_links", "flags")

FIELDS = [
    "avatars",
    "base_url",
    "default_user_change_name",
    "default_user_change_email",
    "default_user_change_username",
    "event_retention",
    "reputation_lower_limit",
    "reputation_upper_limit",
    "footer_links",
    "gdpr_compliance",
    "impersonation",
    "impersonation_require_reason",
    "default_token_duration",
    "default_token_length",
    "pagination_default_page_size",
    "pagination_max_page_size",
    "flags",
]


def create_system_settings(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    SystemSettings = apps.get_model("authentik_admin", "SystemSettings")
    if SystemSettings.objects.using(db_alias).exists():
        return

    settings = {}
    with connections[db_alias].cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name = 'authentik_tenants_tenant'"
        )
        if cursor.fetchone() is not None:
            cursor.execute(
                f"SELECT {', '.join(FIELDS)} FROM authentik_tenants_tenant WHERE schema_name = %s",  # nosec
                [CONFIG.get("postgresql.default_schema")],
            )
            tenant = cursor.fetchone()
            if tenant is not None:
                settings = dict(zip(FIELDS, tenant, strict=True))
                # The raw cursor returns jsonb as str, which JSONField would encode again
                for field in JSON_FIELDS:
                    if isinstance(settings[field], str):
                        settings[field] = loads(settings[field])

    SystemSettings.objects.using(db_alias).create(**settings)


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_admin", "0001_initial"),
        # Carries the settings this migration copies, including `flags`
        ("authentik_tenants", "0009_alter_tenant_base_url"),
        # Sets the `setup` flag, which must be copied along with the others
        ("authentik_core", "0058_setup"),
    ]

    operations = [
        migrations.RunPython(code=create_system_settings, reverse_code=migrations.RunPython.noop),
    ]
