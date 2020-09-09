#!/usr/bin/env python
"""System Migration handler"""
from importlib.util import module_from_spec, spec_from_file_location
from inspect import getmembers, isclass
from pathlib import Path
from typing import Any

from psycopg2 import connect
from structlog import get_logger

from passbook.lib.config import CONFIG

LOGGER = get_logger()


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
    )
    curr = conn.cursor()

    for migration in Path(__file__).parent.absolute().glob("system_migrations/*.py"):
        spec = spec_from_file_location("lifecycle.system_migrations", migration)
        mod = module_from_spec(spec)
        # pyright: reportGeneralTypeIssues=false
        spec.loader.exec_module(mod)

        for _, sub in getmembers(mod, isclass):
            migration = sub(curr, conn)
            if migration.needs_migration():
                LOGGER.info("Migration needs to be applied", migration=sub)
                migration.run()
                LOGGER.info("Migration finished applying", migration=sub)
