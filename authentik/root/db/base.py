"""authentik database backend"""

from django.core.checks import Warning
from django.db.backends.base.validation import BaseDatabaseValidation
from django_tenants.postgresql_backend.base import DatabaseWrapper as BaseDatabaseWrapper

from authentik.lib.config import CONFIG


class DatabaseValidation(BaseDatabaseValidation):

    def check(self, **kwargs):
        return self._check_encoding()

    def _check_encoding(self):
        """Throw a warning when the server_encoding is not UTF-8 or
        server_encoding and client_encoding are mismatched"""
        messages = []
        with self.connection.cursor() as cursor:
            cursor.execute("SHOW server_encoding;")
            server_encoding = cursor.fetchone()[0]
            cursor.execute("SHOW client_encoding;")
            client_encoding = cursor.fetchone()[0]
            if server_encoding != client_encoding:
                messages.append(
                    Warning(
                        "PostgreSQL Server and Client encoding are mismatched: Server: "
                        f"{server_encoding}, Client: {client_encoding}",
                        id="ak.db.W001",
                    )
                )
            if server_encoding != "UTF8":
                messages.append(
                    Warning(
                        f"PostgreSQL Server encoding is not UTF8: {server_encoding}",
                        id="ak.db.W002",
                    )
                )
        return messages


class DatabaseWrapper(BaseDatabaseWrapper):
    """database backend which supports rotating credentials"""

    validation_class = DatabaseValidation

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
