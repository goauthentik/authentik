from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_brands", "0013_brandclientcertificate_and_more"),
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
                    "Supports XYZ templates with {z}, {x} and {y} placeholders, or "
                    "pmtiles:// archive URLs. When empty, the frontend uses the "
                    "bundled hexworld basemap."
                ),
            ),
        ),
    ]
