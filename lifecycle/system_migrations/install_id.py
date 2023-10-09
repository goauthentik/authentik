# flake8: noqa
from uuid import uuid4

from authentik.lib.config import CONFIG
from lifecycle.migrate import BaseMigration

SQL_STATEMENT = """BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS authentik_install_id (
    id TEXT NOT NULL
);
COMMIT;"""


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            "select * from information_schema.tables where table_name = 'authentik_install_id';"
        )
        return not bool(self.cur.rowcount)

    def upgrade(self, migrate=False):
        self.cur.execute(SQL_STATEMENT)
        with self.con.transaction():
            if migrate:
                # If we already have migrations in the database, assume we're upgrading an existing install
                # and set the install id to the secret key
                self.cur.execute(
                    "INSERT INTO authentik_install_id (id) VALUES (%s)", (CONFIG.get("secret_key"),)
                )
            else:
                # Otherwise assume a new install, generate an install ID based on a UUID
                install_id = str(uuid4())
                self.cur.execute("INSERT INTO authentik_install_id (id) VALUES (%s)", (install_id,))

    def run(self):
        self.cur.execute(
            "select * from information_schema.tables where table_name = 'django_migrations';"
        )
        if not bool(self.cur.rowcount):
            # No django_migrations table, so generate a new id
            return self.upgrade(migrate=False)
        self.cur.execute("select count(*) from django_migrations;")
        migrations = self.cur.fetchone()[0]
        return self.upgrade(migrate=migrations > 0)
