"""Seed activity from retained successful events without relying on event retention afterward."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_core", "0067_useractivity"),
        ("authentik_events", "0020_alter_event_action"),
    ]
    operations = [
        migrations.RunSQL(
            """
        INSERT INTO authentik_core_useractivity AS activity (user_id, last_activity_at)
        SELECT users.id, MAX(events.created)
        FROM authentik_core_user users
        JOIN authentik_events_event events ON events.user->'pk' = to_jsonb(users.id)
        WHERE events.action IN ('login', 'authorize_application')
        GROUP BY users.id
        ON CONFLICT (user_id) DO UPDATE
        SET last_activity_at = GREATEST(activity.last_activity_at, EXCLUDED.last_activity_at)
        """,
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
