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
LOCKED = False


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


def wait_for_lock():
    """lock an advisory lock to prevent multiple instances from migrating at once"""
    LOGGER.info("waiting to acquire database lock")
    curr.execute("SELECT pg_advisory_lock(%s)", (ADV_LOCK_UID,))
    # pylint: disable=global-statement
    global LOCKED
    LOCKED = True


def release_lock():
    """Release database lock"""
    if not LOCKED:
        return
    curr.execute("SELECT pg_advisory_unlock(%s)", (ADV_LOCK_UID,))


if __name__ == "__main__":
    conn = connect(
        dbname=CONFIG.get("postgresql.name"),
        user=CONFIG.get("postgresql.user"),
        password=CONFIG.get("postgresql.password"),
        host=CONFIG.get("postgresql.host"),
        port=int(CONFIG.get("postgresql.port")),
        sslmode=CONFIG.get("postgresql.sslmode"),
        sslrootcert=CONFIG.get("postgresql.sslrootcert"),
        sslcert=CONFIG.get("postgresql.sslcert"),
        sslkey=CONFIG.get("postgresql.sslkey"),
    )
    curr = conn.cursor()
    try:
        for migration in Path(__file__).parent.absolute().glob("system_migrations/*.py"):
            spec = spec_from_file_location("lifecycle.system_migrations", migration)
            if not spec:
                continue
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)

            for name, sub in getmembers(mod, isclass):
                if name != "Migration":
                    continue
                migration = sub(curr, conn)
                if migration.needs_migration():
                    wait_for_lock()
                    LOGGER.info("Migration needs to be applied", migration=sub)
                    migration.run()
                    LOGGER.info("Migration finished applying", migration=sub)
                    release_lock()
        LOGGER.info("applying django migrations")
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
        wait_for_lock()
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
        release_lock()
