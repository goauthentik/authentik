from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from authentik.lib.migrations import progress_bar
from authentik.lib.utils.db import chunked_queryset


def create_password_devices(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
    User = apps.get_model("authentik_core", "User")
    PasswordDevice = apps.get_model("authentik_stages_password", "PasswordDevice")

    db_alias = schema_editor.connection.alias
    users = User.objects.using(db_alias).only(
        "pk", "password", "password_change_date", "last_login"
    )
    print("\nMigrating user passwords to password devices, this might take a couple of minutes...")
    batch = []
    for user in progress_bar(chunked_queryset(users), total=users.count()):
        batch.append(
            PasswordDevice(
                user_id=user.pk,
                name="Password",
                password=user.password,
                password_change_date=user.password_change_date,
                last_used=user.last_login,
            )
        )
        if len(batch) >= 1000:
            PasswordDevice.objects.using(db_alias).bulk_create(batch)
            batch = []
    if batch:
        PasswordDevice.objects.using(db_alias).bulk_create(batch)


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_stages_password", "0011_passworddevice"),
    ]

    # Irreversible on purpose: the User.password column is no longer written once devices
    # exist, so reversing would revert users to stale or missing password hashes.
    operations = [migrations.RunPython(create_password_devices)]
