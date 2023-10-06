# flake8: noqa
from lifecycle.migrate import BaseMigration

SQL_STATEMENT = """ALTER TABLE authentik_audit_event RENAME TO authentik_events_event;
UPDATE django_migrations SET app = replace(app, 'authentik_audit', 'authentik_events');
UPDATE django_content_type SET app_label = replace(app_label, 'authentik_audit', 'authentik_events');"""


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            "select * from information_schema.tables where table_name = 'authentik_audit_event';"
        )
        return bool(self.cur.rowcount)

    def run(self):
        with self.con.transaction():
            self.cur.execute(SQL_STATEMENT)
