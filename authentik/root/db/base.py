"""authentik database backend"""

from django_tenants.postgresql_backend.base import DatabaseWrapper as BaseDatabaseWrapper

from authentik.common.config import CONFIG


class DatabaseWrapper(BaseDatabaseWrapper):
    """database backend which supports rotating credentials"""

    def get_connection_params(self):
        """Refresh DB credentials before getting connection params"""
        conn_params = super().get_connection_params()

        prefix = "postgresql"
        if self.alias.startswith("replica_"):
            prefix = f"postgresql.read_replicas.{self.alias.removeprefix('replica_')}"

        for setting in ("host", "port", "user", "password"):
            conn_params[setting] = CONFIG.refresh(f"{prefix}.{setting}")
            if conn_params[setting] is None and self.alias.startswith("replica_"):
                conn_params[setting] = CONFIG.refresh(f"postgresql.{setting}")

        return conn_params
