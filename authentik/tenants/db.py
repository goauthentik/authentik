from random import choice

from django.conf import settings


class FailoverRouter:
    """Support an primary/read-replica PostgreSQL setup (reading from replicas
    and write to primary only)"""

    def __init__(self) -> None:
        super().__init__()
        self.database_aliases = set(settings.DATABASES.keys())
        self.read_replica_aliases = list(self.database_aliases - {"default"})
        self.replica_enabled = len(self.read_replica_aliases) > 0

    def db_for_read(self, model, **hints):
        if not self.replica_enabled:
            return "default"
        return choice(self.read_replica_aliases)  # nosec

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """Relations between objects are allowed if both objects are
        in the primary/replica pool."""
        if obj1._state.db in self.database_aliases and obj2._state.db in self.database_aliases:
            return True
        return None
