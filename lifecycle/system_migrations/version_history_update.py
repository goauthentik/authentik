# flake8: noqa
from lifecycle.migrate import BaseMigration
from datetime import datetime

from authentik import __version__, get_build_hash


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            """
            SELECT * FROM authentik_version_history
                WHERE version = %s AND build = %s
                ORDER BY "timestamp" DESC
                LIMIT 1
        """,
            (__version__, get_build_hash()),
        )
        return not bool(self.cur.rowcount)

    def run(self):
        self.cur.execute(
            """
            INSERT INTO authentik_version_history ("timestamp", version, build)
                VALUES (%s, %s, %s)
        """,
            (datetime.now(), __version__, get_build_hash()),
        )
        self.cur.execute(
            """
            DELETE FROM authentik_version_history WHERE id NOT IN (
                SELECT id FROM authentik_version_history
                ORDER BY "timestamp" DESC
                LIMIT 1000
            )
        """
        )
        self.con.commit()
