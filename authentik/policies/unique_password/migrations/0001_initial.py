# Generated by Django 5.0.7 on 2024-08-02 04:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("authentik_policies", "0011_policybinding_failure_result_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="UniquePasswordPolicy",
            fields=[
                (
                    "policy_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="authentik_policies.policy",
                    ),
                ),
                (
                    "password_field",
                    models.TextField(
                        default="password",
                        help_text="Field key to check, field keys defined in Prompt stages are available.",
                    ),
                ),
                (
                    "num_historical_passwords",
                    models.PositiveIntegerField(
                        default=0, help_text="Number of passwords to check against."
                    ),
                ),
            ],
            options={
                "verbose_name": "Password Uniqueness Policy",
                "verbose_name_plural": "Password Uniqueness Policies",
                "indexes": [
                    models.Index(fields=["policy_ptr_id"], name="authentik_p_policy__f559aa_idx")
                ],
            },
            bases=("authentik_policies.policy",),
        ),
    ]