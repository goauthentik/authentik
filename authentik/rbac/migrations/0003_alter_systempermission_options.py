# Generated by Django 4.2.8 on 2023-12-20 10:02

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_rbac", "0002_systempermission"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="systempermission",
            options={
                "default_permissions": (),
                "managed": False,
                "permissions": [
                    ("view_system_info", "Can view system info"),
                    ("view_system_tasks", "Can view system tasks"),
                    ("run_system_tasks", "Can run system tasks"),
                    ("access_admin_interface", "Can access admin interface"),
                    ("view_system_settings", "Can view system settings"),
                    ("edit_system_settings", "Can edit system settings"),
                ],
                "verbose_name": "System permission",
                "verbose_name_plural": "System permissions",
            },
        ),
    ]
