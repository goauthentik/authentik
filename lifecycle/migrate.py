#!/usr/bin/env python
"""System Migration handler"""

from importlib.util import module_from_spec, spec_from_file_location
from inspect import getmembers, isclass
from os import environ, system
from pathlib import Path
from typing import Any

from packaging.version import Version
from psycopg import Connection, Cursor, connect
from structlog.stdlib import get_logger

from authentik import authentik_version, authentik_version_previous_major
from authentik.lib.config import CONFIG, django_db_config, postgresql_direct_connection_kwargs

LOGGER = get_logger()
ADV_LOCK_UID = 1000
LOCKED = False


class CommandError(Exception):
    """Error raised when a system_crit command fails"""


class BaseMigration:
    """Base System Migration"""

    cur: Cursor
    con: Connection

    def __init__(self, cur: Any, con: Any):
        self.cur = cur
        self.con = con
        self.log = get_logger().bind()

    def system_crit(self, command: str):
        """Run system command"""
        self.log.debug("Running system_crit command", command=command)
        retval = system(command)  # nosec
        if retval != 0:
            raise CommandError("Migration error")

    def fake_migration(self, *app_migration: tuple[str, str]):
        """Fake apply a list of migrations, arguments are
        expected to be tuples of (app_label, migration_name)"""
        for app, _migration in app_migration:
            self.system_crit(f"./manage.py migrate {app} {_migration} --fake")

    def needs_migration(self) -> bool:
        """Return true if Migration needs to be run"""
        return False

    def run(self):
        """Run the actual migration"""


def wait_for_lock(conn: Connection, cursor: Cursor):
    """lock an advisory lock to prevent multiple instances from migrating at once"""
    global LOCKED  # noqa: PLW0603
    LOGGER.info("waiting to acquire database lock")
    with conn.transaction():
        cursor.execute("SELECT pg_advisory_lock(%s)", (ADV_LOCK_UID,))
    LOCKED = True


def release_lock(conn: Connection, cursor: Cursor):
    """Release database lock"""
    global LOCKED  # noqa: PLW0603
    if not LOCKED:
        return
    LOGGER.info("releasing database lock")
    with conn.transaction():
        cursor.execute("SELECT pg_advisory_unlock(%s)", (ADV_LOCK_UID,))
    LOCKED = False


def ensure_allowed_version(cursor: Cursor) -> None:
    """During an upgrade, ensure that major (i.e. semver-minor) versions were not skipped."""
    cursor.execute(
        "SELECT * FROM information_schema.tables WHERE table_name = 'authentik_version_history';"
    )
    if not cursor.rowcount:
        return
    cursor.execute("SELECT version FROM authentik_version_history ORDER BY timestamp DESC LIMIT 1")
    if not cursor.rowcount:
        return

    db_version = Version(cursor.fetchone()[0])
    previous_code_version = Version(authentik_version_previous_major())
    current_code_version = Version(authentik_version())

    # Downgrades are not supported, but we don't stop them (for now)
    if db_version > current_code_version:
        LOGGER.warning(
            "Unsupported downgrade detected",
            downgrading_from=db_version,
            downgrading_to=current_code_version,
        )

    if (
        db_version.major == previous_code_version.major
        and db_version.minor == previous_code_version.minor
    ) or (
        db_version.major == current_code_version.major
        and db_version.minor == current_code_version.minor
    ):
        return

    message = "Major version skips are not allowed. Please upgrade one major version at a time."
    LOGGER.error(message, upgrading_from=db_version, upgrading_to=current_code_version)
    raise RuntimeError(message)


def run_migrations():
    if CONFIG.get_bool("skip_migrations", False):
        return
    # `wait_for_lock` issues `pg_advisory_lock(1000)` and holds it for the full
    # migrate + check pass. Open this against the direct endpoint when
    # configured, otherwise a transaction-pooling pooler in front of
    # ``postgresql.host`` would make the session-scoped lock unreachable.
    conn = connect(**postgresql_direct_connection_kwargs(CONFIG))
    curr = conn.cursor()
    try:
        wait_for_lock(conn, curr)
        ensure_allowed_version(curr)
        for migration_path in sorted(
            Path(__file__).parent.absolute().glob("system_migrations/*.py")
        ):
            spec = spec_from_file_location("lifecycle.system_migrations", migration_path)
            if not spec:
                continue
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)

            for name, sub in getmembers(mod, isclass):
                if name != "Migration":
                    continue
                migration = sub(curr, conn)
                curr.execute(f"SET search_path = {CONFIG.get('postgresql.default_schema')}")
                if migration.needs_migration():
                    LOGGER.info("Migration needs to be applied", migration=migration_path.name)
                    migration.run()
                    LOGGER.info("Migration finished applying", migration=migration_path.name)
        LOGGER.info("applying django migrations")
        environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
        try:
            from django.core.management import execute_from_command_line
        except ImportError as exc:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            ) from exc
        execute_from_command_line(["", "migrate_schemas"])
        if CONFIG.get_bool("tenants.enabled", False):
            execute_from_command_line(["", "migrate_schemas", "--schema", "template", "--tenant"])
        # Run django system checks for all databases
        check_args = ["", "check"]
        for label in django_db_config(CONFIG).keys():
            check_args.append(f"--database={label}")
        if not CONFIG.get_bool("debug"):
            check_args.append("--deploy")
        execute_from_command_line(check_args)
    finally:
        release_lock(conn, curr)
        curr.close()
        conn.close()


if __name__ == "__main__":
    run_migrations()
