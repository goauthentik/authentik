from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def migrate_acs_url(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
    SAMLProvider = apps.get_model("authentik_providers_saml", "samlprovider")
    db_alias = schema_editor.connection.alias

    for provider in SAMLProvider.objects.using(db_alias).all():
        provider._acs_urls = [
            {
                "url": provider.legacy_acs_url,
                "matching_mode": "strict",
                "index": None,
                "is_default": True,
            }
        ]
        provider.save(update_fields=["_acs_urls"])


def reverse_migrate_acs_url(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
    SAMLProvider = apps.get_model("authentik_providers_saml", "samlprovider")
    db_alias = schema_editor.connection.alias

    for provider in SAMLProvider.objects.using(db_alias).all():
        strict = [entry for entry in provider._acs_urls if entry.get("matching_mode") == "strict"]
        default = next((entry for entry in strict if entry.get("is_default")), None)
        if not default and strict:
            default = strict[0]
        provider.legacy_acs_url = default["url"] if default else ""
        provider.save(update_fields=["legacy_acs_url"])


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_providers_saml", "0024_samlprovider_jwt_federation_providers"),
    ]

    operations = [
        migrations.AddField(
            model_name="samlprovider",
            name="_acs_urls",
            field=models.JSONField(
                default=list,
                help_text=(
                    "Assertion Consumer Service URLs the provider may send responses to. The "
                    "default entry is used for IdP-initiated logins and requests without an ACS "
                    "URL."
                ),
                verbose_name="ACS URLs",
            ),
        ),
        # `acs_url` is replaced by `_acs_urls`. Keep the column for instances still running a
        # previous version during an upgrade, and drop it in a later release.
        migrations.AlterField(
            model_name="samlprovider",
            name="acs_url",
            field=models.TextField(
                db_column="acs_url",
                default="",
                help_text="Deprecated, use ACS URLs instead.",
                verbose_name="ACS URL (deprecated)",
            ),
        ),
        migrations.RenameField(
            model_name="samlprovider",
            old_name="acs_url",
            new_name="legacy_acs_url",
        ),
        migrations.RunPython(migrate_acs_url, reverse_migrate_acs_url),
    ]
