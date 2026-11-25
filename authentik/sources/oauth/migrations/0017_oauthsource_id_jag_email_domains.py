import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_core", "0068_move_source_icons"),
        ("authentik_sources_oauth", "0016_alter_oauthsource_consumer_secret"),
    ]

    operations = [
        migrations.AddField(
            model_name="oauthsource",
            name="id_jag_email_domains",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.TextField(),
                blank=True,
                db_default=[],
                default=list,
                help_text=(
                    "Email domains this source is trusted for when redeeming ID-JAGs. An ID-JAG "
                    "whose subject isn't connected to a user yet is connected to the one active "
                    "user with its email address, if that address is in one of these domains."
                ),
                size=None,
                verbose_name="ID-JAG email domains",
            ),
        ),
        migrations.AddField(
            model_name="oauthsource",
            name="id_jag_email_group",
            field=models.ForeignKey(
                blank=True,
                db_index=False,
                help_text=(
                    "ID-JAG email addresses only match users connected to an enabled source, "
                    "such as a directory, or members of this group, as users who registered "
                    "themselves may not own their address."
                ),
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="authentik_core.group",
                verbose_name="ID-JAG email group",
            ),
        ),
    ]
