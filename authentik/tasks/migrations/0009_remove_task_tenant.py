from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_tasks", "0008_remove_task_update_aggregated_status_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name="task",
                    name="tenant",
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE "authentik_tasks_task" ALTER COLUMN "tenant_id" DROP NOT NULL',
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
