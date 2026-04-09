from random import choice

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections


class FailoverRouter:
    """Support an primary/read-replica PostgreSQL setup (reading from replicas
    and write to primary only)"""

    def __init__(self) -> None:
        super().__init__()
        self.database_aliases = set(settings.DATABASES.keys())
        self.read_replica_aliases = list(self.database_aliases - {DEFAULT_DB_ALIAS})
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
