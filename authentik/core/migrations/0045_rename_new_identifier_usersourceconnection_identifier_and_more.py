from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_core", "0044_usersourceconnection_new_identifier"),
        ("authentik_sources_kerberos", "0003_migrate_userkerberossourceconnection_identifier"),
        ("authentik_sources_oauth", "0009_migrate_useroauthsourceconnection_identifier"),
        ("authentik_sources_plex", "0005_migrate_userplexsourceconnection_identifier"),
        ("authentik_sources_saml", "0019_migrate_usersamlsourceconnection_identifier"),
    ]

    operations = [
        migrations.RenameField(
            model_name="usersourceconnection",
            old_name="new_identifier",
            new_name="identifier",
        ),
        migrations.AddIndex(
            model_name="usersourceconnection",
            index=models.Index(fields=["identifier"], name="authentik_c_identif_59226f_idx"),
        ),
        migrations.AddIndex(
            model_name="usersourceconnection",
            index=models.Index(
                fields=["source", "identifier"], name="authentik_c_source__649e04_idx"
            ),
        ),
    ]
