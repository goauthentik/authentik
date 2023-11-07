from django.db import migrations, models

import authentik.lib.generators
from authentik.lib.config import CONFIG


def create_default_tenant(apps, schema_editor):
    Tenant = apps.get_model("authentik_tenants", "Tenant")
    db_alias = schema_editor.connection.alias
    Tenant.objects.using(db_alias).create(
        domain_regex=".*",
        avatars=CONFIG.get("avatars", "gravatar,initials"),
        default_user_change_name=CONFIG.get_bool("user_change_name", True),
        default_user_change_email=CONFIG.get_bool("user_change_email", False),
        default_user_change_username=CONFIG.get_bool("user_change_email", False),
        gdpr_compliance=CONFIG.get_bool("gdpr_compliance", True),
        impersonation=CONFIG.get_bool("impersonation", True),
        footer_links=CONFIG.get("footer_links", default=[]),
    )


def delete_all_tenants(apps, schema_editor):
    Tenant = apps.get_model("authentik_tenants", "Tenant")
    db_alias = schema_editor.connection.alias
    Tenant.objects.using(db_alias).all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_tenants", "0005_tenant_to_brand"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="tenant",
            name="attributes",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="branding_favicon",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="branding_logo",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="branding_title",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="default",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="domain",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="event_retention",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="flow_authentication",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="flow_device_code",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="flow_invalidation",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="flow_recovery",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="flow_unenrollment",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="flow_user_settings",
        ),
        migrations.RemoveField(
            model_name="tenant",
            name="web_certificate",
        ),
        migrations.AddField(
            model_name="tenant",
            name="avatars",
            field=models.TextField(
                default="gravatar,initials",
                help_text="Configure how authentik should show avatars for users.",
            ),
        ),
        migrations.AddField(
            model_name="tenant",
            name="domain_regex",
            field=models.TextField(
                default="*", help_text="Domain regex that activates this tenant."
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="tenant",
            name="footer_links",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="The option configures the footer links on the flow executor pages.",
            ),
        ),
        migrations.AddField(
            model_name="tenant",
            name="gdpr_compliance",
            field=models.BooleanField(
                default=True,
                help_text="When enabled, all the events caused by a user will be deleted upon the user's deletion.",
            ),
        ),
        migrations.AddField(
            model_name="tenant",
            name="impersonation",
            field=models.BooleanField(
                default=True, help_text="Globally enable/disable impersonation."
            ),
        ),
        migrations.AddField(
            model_name="tenant",
            name="default_user_change_email",
            field=models.BooleanField(
                default=False,
                help_text="Enable the ability for users to change their email address.",
            ),
        ),
        migrations.AddField(
            model_name="tenant",
            name="default_user_change_name",
            field=models.BooleanField(
                default=True, help_text="Enable the ability for users to change their name."
            ),
        ),
        migrations.AddField(
            model_name="tenant",
            name="default_user_change_username",
            field=models.BooleanField(
                default=False, help_text="Enable the ability for users to change their username."
            ),
        ),
        migrations.RunPython(code=create_default_tenant, reverse_code=delete_all_tenants),
    ]
