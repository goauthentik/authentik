from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_brands", "0015_brand_flow_user_switch"),
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
                    "bundled hexworld basemap. This value is part of the brand "
                    "information served to unauthenticated clients; do not embed API "
                    "keys or other credentials in it."
                ),
            ),
        ),
    ]
