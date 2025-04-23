from django.db import migrations


def migrate_identifier(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    UserPlexSourceConnection = apps.get_model("authentik_sources_plex", "UserPlexSourceConnection")

    for connection in UserPlexSourceConnection.objects.using(db_alias).all():
        connection.new_identifier = connection.identifier
        connection.save(using=db_alias)


class Migration(migrations.Migration):

    dependencies = [
        (
            "authentik_sources_plex",
            "0004_groupplexsourceconnection_plexsourcepropertymapping_and_more",
        ),
        ("authentik_core", "0044_usersourceconnection_new_identifier"),
    ]

    operations = [
        migrations.RunPython(code=migrate_identifier, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="userplexsourceconnection",
            name="identifier",
        ),
    ]
