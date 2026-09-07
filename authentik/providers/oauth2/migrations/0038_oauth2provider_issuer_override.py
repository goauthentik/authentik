from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_providers_oauth2", "0037_accesstoken_actor_authorizationcode_actor_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="oauth2provider",
            name="issuer_override",
            field=models.TextField(
                blank=True,
                default="",
                help_text=(
                    "Use this exact value as the issuer instead of deriving one from Issuer "
                    "mode. Leave empty to use Issuer mode. Set this when several providers must "
                    "share a single issuer, for example an application whose desktop and mobile "
                    "clients ship their own fixed client IDs and therefore need one provider "
                    "each, while the application itself only trusts a single issuer."
                ),
            ),
        ),
    ]
