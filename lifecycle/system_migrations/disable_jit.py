from psycopg import Error, sql

from lifecycle.migrate import BaseMigration


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        # Only replace PostgreSQL's built-in default; an explicitly configured jit wins
        self.cur.execute("""
            SELECT 1 FROM pg_settings
                WHERE name = 'jit' AND setting = 'on' AND source = 'default'
        """)
        return bool(self.cur.rowcount)

    def run(self):
        self.cur.execute("SELECT session_user, current_database()")
        role, database = self.cur.fetchone()
        statement = sql.SQL("ALTER ROLE {} IN DATABASE {} SET jit = off").format(
            sql.Identifier(role), sql.Identifier(database)
        )
        try:
            with self.con.transaction():
                self.cur.execute(statement)
        except Error as exc:
            self.log.warning(
                "Failed to disable PostgreSQL JIT, run this statement or set jit explicitly",
                statement=statement.as_string(self.con),
                exc=exc,
            )
        self.con.commit()
