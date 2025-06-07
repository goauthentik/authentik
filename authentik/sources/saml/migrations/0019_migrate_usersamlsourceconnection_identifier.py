from django.db import migrations


def migrate_identifier(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    UserSAMLSourceConnection = apps.get_model("authentik_sources_saml", "UserSAMLSourceConnection")

    for connection in UserSAMLSourceConnection.objects.using(db_alias).all():
        connection.new_identifier = connection.identifier
        connection.save(using=db_alias)


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_sources_saml", "0018_alter_samlsource_slo_url_alter_samlsource_sso_url"),
        ("authentik_core", "0044_usersourceconnection_new_identifier"),
    ]

    operations = [
        migrations.RunPython(code=migrate_identifier, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="usersamlsourceconnection",
            name="identifier",
        ),
    ]
