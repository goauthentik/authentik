from django.db import migrations, models

APP = "authentik_endpoints_connectors_agent"


def carry_over_boolean(apps, schema_editor):
    AgentConnector = apps.get_model(APP, "AgentConnector")
    AgentConnector.objects.filter(apple_psso_require_biometrics=True).update(
        apple_psso_biometric_requirement="current_set"
    )


def restore_boolean(apps, schema_editor):
    AgentConnector = apps.get_model(APP, "AgentConnector")
    AgentConnector.objects.exclude(apple_psso_biometric_requirement="none").update(
        apple_psso_require_biometrics=True
    )


class Migration(migrations.Migration):

    dependencies = [
        (
            "authentik_endpoints_connectors_agent",
            "0009_agentconnector_apple_psso_require_biometrics",
        ),
    ]

    operations = [
        # Preserve intent for anyone already running 0009: a connector with biometrics
        # switched on keeps a requirement, and gains the password fallback that the
        # boolean never offered.
        migrations.AddField(
            model_name="agentconnector",
            name="apple_psso_biometric_requirement",
            field=models.TextField(
                choices=[
                    ("none", "None (no biometric required)"),
                    (
                        "current_set",
                        "Touch ID or Apple Watch, invalidated if enrolment changes",
                    ),
                    ("any", "Touch ID or Apple Watch, any enrolment"),
                ],
                default="none",
            ),
        ),
        migrations.AddField(
            model_name="agentconnector",
            name="apple_psso_biometric_password_fallback",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="agentconnector",
            name="apple_psso_biometric_reuse_during_unlock",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(carry_over_boolean, restore_boolean),
        migrations.RemoveField(
            model_name="agentconnector",
            name="apple_psso_require_biometrics",
        ),
    ]
