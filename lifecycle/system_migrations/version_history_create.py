# flake8: noqa
from lifecycle.migrate import BaseMigration


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            "SELECT * FROM information_schema.tables WHERE table_name = 'authentik_version_history';"
        )
        return not bool(self.cur.rowcount)

    def run(self):
        self.cur.execute(
            """
            BEGIN TRANSACTION;
                CREATE TABLE IF NOT EXISTS authentik_version_history (
                    id BIGSERIAL PRIMARY KEY,
                    "timestamp" timestamp with time zone NOT NULL,
                    version text NOT NULL,
                    build text NOT NULL
                );
            COMMIT;
        """
        )
