from django.db import migrations, models

OLD_SUBJECT = "authentik Sign-in code"
NEW_SUBJECT = "Your verification code is {{ token }}"


def update_default_subject(apps, schema_editor):
    AuthenticatorEmailStage = apps.get_model(
        "authentik_stages_authenticator_email", "AuthenticatorEmailStage"
    )
    db_alias = schema_editor.connection.alias
    AuthenticatorEmailStage.objects.using(db_alias).filter(subject=OLD_SUBJECT).update(
        subject=NEW_SUBJECT
    )


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_stages_authenticator_email", "0004_alter_emaildevice_stage"),
    ]

    operations = [
        migrations.AlterField(
            model_name="authenticatoremailstage",
            name="subject",
            field=models.TextField(default=NEW_SUBJECT),
        ),
        migrations.RunPython(update_default_subject, migrations.RunPython.noop),
    ]
