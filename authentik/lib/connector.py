"""Fix dbbackup quoting the password"""
from dbbackup.db.postgresql import PgDumpConnector


class PgCustom(PgDumpConnector):
    """Fix dbbackup quoting the password"""

    def run_command(self, *args, **kwargs):
        if self.settings.get("PASSWORD"):
            env = kwargs.get("env", {})
            env["PGPASSWORD"] = self.settings["PASSWORD"]
            kwargs["env"] = env
        return super(PgDumpConnector, self).run_command(*args, **kwargs)
