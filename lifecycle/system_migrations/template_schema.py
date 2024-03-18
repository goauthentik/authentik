from lifecycle.migrate import BaseMigration


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        return True

    def run(self):
        self.cur.execute("CREATE SCHEMA IF NOT EXISTS template;")
