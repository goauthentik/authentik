import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
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
    ]
