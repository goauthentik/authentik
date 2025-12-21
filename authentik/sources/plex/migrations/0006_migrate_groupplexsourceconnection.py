from django.db import migrations


def create_missing_groupplexsourceconnection(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    GroupSourceConnection = apps.get_model("authentik_core", "GroupSourceConnection")
    PlexSource = apps.get_model("authentik_sources_plex", "PlexSource")
    GroupPlexSourceConnection = apps.get_model(
        "authentik_sources_plex", "GroupPlexSourceConnection"
    )

    for source in PlexSource.objects.using(db_alias).all():
        for gsc in GroupSourceConnection.objects.using(db_alias).filter(source=source):
            if GroupPlexSourceConnection.objects.using(db_alias).filter(pk=gsc.pk).exists():
                continue
            gpsc = GroupPlexSourceConnection(pk=gsc.pk)
            gpsc.save(using=db_alias)


class Migration(migrations.Migration):

    dependencies = [
        (
            "authentik_sources_plex",
            "0005_migrate_userplexsourceconnection_identifier",
        ),
        ("authentik_core", "0044_usersourceconnection_new_identifier"),
    ]

    operations = [
        migrations.RunPython(
            code=create_missing_groupplexsourceconnection, reverse_code=migrations.RunPython.noop
        ),
    ]
