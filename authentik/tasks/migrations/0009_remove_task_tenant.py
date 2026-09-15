from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_tasks", "0008_remove_task_update_aggregated_status_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="task",
            name="tenant",
        ),
    ]
