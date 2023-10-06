# flake8: noqa
from lifecycle.migrate import BaseMigration

SQL_STATEMENT = """DROP TABLE "authentik_policies_hibp_haveibeenpwendpolicy";
DELETE FROM django_migrations WHERE app = 'authentik_policies_hibp';"""


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            "SELECT * FROM information_schema.tables WHERE table_name ="
            " 'authentik_policies_hibp_haveibeenpwendpolicy';"
        )
        return bool(self.cur.rowcount)

    def run(self):
        with self.con.transaction():
            self.cur.execute(SQL_STATEMENT)
