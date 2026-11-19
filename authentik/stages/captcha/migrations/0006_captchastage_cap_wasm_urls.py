from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_stages_captcha", "0005_captchastage_request_content_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="captchastage",
            name="cap_hashwx_wasm_url",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="captchastage",
            name="cap_wasm_url",
            field=models.TextField(blank=True, default=""),
        ),
    ]
