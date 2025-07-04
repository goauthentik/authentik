# Generated by Django 5.1.11 on 2025-07-03 13:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_core", "0048_delete_oldauthenticatedsession_content_type"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="token",
            options={
                "permissions": [
                    ("view_token_key", "View token's key"),
                    ("set_token_key", "Set a token's key"),
                ],
                "verbose_name": "Token",
                "verbose_name_plural": "Tokens",
            },
        ),
    ]
