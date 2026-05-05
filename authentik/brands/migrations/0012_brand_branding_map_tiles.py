from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_brands", "0011_alter_brand_branding_default_flow_background_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="brand",
            name="branding_map_tiles",
            field=models.TextField(
                blank=True,
                default="",
                help_text=(
                    "URL template for the vector tile source used by the events map. "
                    "Supports the {z}, {x} and {y} placeholders. "
                    "When empty, the frontend falls back to the proxied default."
                ),
            ),
        ),
    ]
