# flake8: noqa
from lifecycle.migrate import BaseMigration

SQL_STATEMENT = """
BEGIN TRANSACTION;
ALTER TABLE IF EXISTS authentik_tenants_tenant RENAME TO authentik_brands_brand;
UPDATE django_migrations SET app = replace(app, 'authentik_tenants', 'authentik_brands');
UPDATE django_content_type SET app_label = replace(app_label, 'authentik_tenants', 'authentik_brands');
COMMIT;
"""


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            "select * from information_schema.tables where table_name = 'django_migrations';"
        )
        # No migration table, assume new installation
        if not bool(self.cur.rowcount):
            return False
        self.cur.execute("select * from django_migrations where app = 'authentik_brands';")
        return not bool(self.cur.rowcount)

    def run(self):
        self.cur.execute(SQL_STATEMENT)
