import pgtrigger.compiler
import pgtrigger.migrations
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "authentik_core",
            "0057_remove_user_groups_remove_user_user_permissions_and_more",
        ),
    ]

    operations = [
        # Update the trigger function to use the public schema prefix,
        # ensuring it works correctly when search_path differs.
        pgtrigger.migrations.RemoveTrigger(
            model_name="groupparentagenode",
            name="refresh_groupancestry",
        ),
        pgtrigger.migrations.AddTrigger(
            model_name="groupparentagenode",
            trigger=pgtrigger.compiler.Trigger(
                name="refresh_groupancestry",
                sql=pgtrigger.compiler.UpsertTriggerSql(
                    func="\n                    REFRESH MATERIALIZED VIEW CONCURRENTLY public.authentik_core_groupancestry;\n                    RETURN NULL;\n                ",
                    hash="f8a6e3b2c1d4a5907b3e2f1c8d6a4b5e9c7d0f1a",
                    operation="INSERT OR UPDATE OR DELETE",
                    pgid="pgtrigger_refresh_groupancestry_62450",
                    table="authentik_core_groupparentage",
                    when="AFTER",
                ),
            ),
        ),
        # Enable the trigger to fire on replicas as well (ALWAYS mode),
        # so that the materialized view is refreshed when data is
        # replicated via PostgreSQL logical replication.
        migrations.RunSQL(
            sql="ALTER TABLE authentik_core_groupparentage ENABLE ALWAYS TRIGGER pgtrigger_refresh_groupancestry_62450;",
            reverse_sql="ALTER TABLE authentik_core_groupparentage ENABLE TRIGGER pgtrigger_refresh_groupancestry_62450;",
        ),
    ]
