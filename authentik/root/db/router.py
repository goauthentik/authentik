from random import choice

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections

from authentik.lib.config import DIRECT_DB_ALIAS


class FailoverRouter:
    """Primary/read-replica routing, with the ``direct`` alias (if configured)
    excluded from replica selection, migrations, and automatic ORM routing.
    The ``direct`` alias is opened explicitly via
    ``connections.create_connection(DIRECT_DB_ALIAS)`` by code that needs a
    stable PG backend (LISTEN/NOTIFY, advisory locks).
    """

    def __init__(self) -> None:
        super().__init__()
        self.database_aliases = set(settings.DATABASES.keys())
        self.read_replica_aliases = list(
            self.database_aliases - {DEFAULT_DB_ALIAS, DIRECT_DB_ALIAS}
        )
        self.replica_enabled = len(self.read_replica_aliases) > 0

    def db_for_read(self, model, **hints):
        if not self.replica_enabled:
            return DEFAULT_DB_ALIAS
        # Stay on primary for the entire transaction to maintain consistency.
        # Reading from a replica mid-transaction would give a different snapshot,
        # breaking transactional semantics (not just read-your-writes, but the
        # entire consistent point-in-time view that a transaction provides).
        if connections[DEFAULT_DB_ALIAS].in_atomic_block:
            return DEFAULT_DB_ALIAS
        return choice(self.read_replica_aliases)  # nosec

    def db_for_write(self, model, **hints):
        return DEFAULT_DB_ALIAS

    def allow_relation(self, obj1, obj2, **hints):
        """Relations between objects are allowed if both objects are
        in the primary/replica pool."""
        if obj1._state.db in self.database_aliases and obj2._state.db in self.database_aliases:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Block migrations against the ``direct`` alias. It points at the same
        underlying database as ``default``; migrations must run via ``default``
        to avoid duplicate work and to avoid taking the migration advisory lock
        against a transaction pooler that can't hold it."""
        if db == DIRECT_DB_ALIAS:
            return False
        return None
