"""authentik database backend"""
from django_prometheus.db.backends.postgresql.base import DatabaseWrapper as BaseDatabaseWrapper

from authentik.lib.config import CONFIG


class DatabaseWrapper(BaseDatabaseWrapper):
    """database backend which supports rotating credentials"""

    def get_connection_params(self):
        CONFIG.refresh("postgresql.password")
        conn_params = super().get_connection_params()
        conn_params["user"] = CONFIG.get("postgresql.user")
        conn_params["password"] = CONFIG.get("postgresql.password")
        return conn_params
