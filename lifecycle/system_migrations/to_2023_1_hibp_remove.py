# flake8: noqa
from lifecycle.migrate import BaseMigration

SQL_STATEMENT = """BEGIN TRANSACTION;
DROP TABLE "authentik_policies_hibp_haveibeenpwendpolicy";
END TRANSACTION;"""


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            "select * from information_schema.tables where table_name = 'authentik_policies_hibp_haveibeenpwendpolicy';"
        )
        return bool(self.cur.rowcount)

    def run(self):
        self.cur.execute(SQL_STATEMENT)
        self.con.commit()
