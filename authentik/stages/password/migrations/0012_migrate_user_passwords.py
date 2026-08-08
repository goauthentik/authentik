from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def create_password_devices(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
    User = apps.get_model("authentik_core", "User")
    PasswordDevice = apps.get_model("authentik_stages_password", "PasswordDevice")

    db_alias = schema_editor.connection.alias
    users = User.objects.using(db_alias).values_list("pk", "password").iterator(chunk_size=1000)
    PasswordDevice.objects.using(db_alias).bulk_create(
        (PasswordDevice(user_id=pk, name="Password", password=password) for pk, password in users),
        batch_size=1000,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_stages_password", "0011_passworddevice"),
    ]

    # Irreversible on purpose: reversing this would leave the re-created User.password
    # column empty, locking every user out.
    operations = [migrations.RunPython(create_password_devices)]
