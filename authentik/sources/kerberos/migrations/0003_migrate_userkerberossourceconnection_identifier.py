from django.db import migrations


def migrate_identifier(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    UserKerberosSourceConnection = apps.get_model(
        "authentik_sources_kerberos", "UserKerberosSourceConnection"
    )

    for connection in UserKerberosSourceConnection.objects.using(db_alias).all():
        connection.new_identifier = connection.identifier
        connection.save(using=db_alias)


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_sources_kerberos", "0002_kerberossource_kadmin_type"),
        ("authentik_core", "0044_usersourceconnection_new_identifier"),
    ]

    operations = [
        migrations.RunPython(code=migrate_identifier, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="userkerberossourceconnection",
            name="identifier",
        ),
    ]
