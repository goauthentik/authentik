from lifecycle.migrate import BaseMigration


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'template';"
        )
        return not bool(self.cur.rowcount)

    def run(self):
        self.cur.execute("CREATE SCHEMA IF NOT EXISTS template; COMMIT;")
