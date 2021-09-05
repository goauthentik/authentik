#!/usr/bin/env python
"""System Migration handler"""
import os
from importlib.util import module_from_spec, spec_from_file_location
from inspect import getmembers, isclass
from pathlib import Path
from typing import Any

from psycopg2 import connect
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()
ADV_LOCK_UID = 1000


class BaseMigration:
    """Base System Migration"""

    cur: Any
    con: Any

    def __init__(self, cur: Any, con: Any):
        self.cur = cur
        self.con = con

    def needs_migration(self) -> bool:
        """Return true if Migration needs to be run"""
        return False

    def run(self):
        """Run the actual migration"""


if __name__ == "__main__":

    conn = connect(
        dbname=CONFIG.y("postgresql.name"),
        user=CONFIG.y("postgresql.user"),
        password=CONFIG.y("postgresql.password"),
        host=CONFIG.y("postgresql.host"),
        port=int(CONFIG.y("postgresql.port")),
    )
    curr = conn.cursor()
    # lock an advisory lock to prevent multiple instances from migrating at once
    LOGGER.info("waiting to acquire database lock")
    curr.execute("SELECT pg_advisory_lock(%s)", (ADV_LOCK_UID,))
    try:
        for migration in Path(__file__).parent.absolute().glob("system_migrations/*.py"):
            spec = spec_from_file_location("lifecycle.system_migrations", migration)
            mod = module_from_spec(spec)
            # pyright: reportGeneralTypeIssues=false
            spec.loader.exec_module(mod)

            for name, sub in getmembers(mod, isclass):
                if name != "Migration":
                    continue
                migration = sub(curr, conn)
                if migration.needs_migration():
                    LOGGER.info("Migration needs to be applied", migration=sub)
                    migration.run()
                    LOGGER.info("Migration finished applying", migration=sub)
        LOGGER.info("applying django migrations")
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
        try:
            from django.core.management import execute_from_command_line
        except ImportError as exc:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            ) from exc
        execute_from_command_line(["", "migrate"])
    finally:
        curr.execute("SELECT pg_advisory_unlock(%s)", (ADV_LOCK_UID,))
