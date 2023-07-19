"""authentik database backend"""
from django_prometheus.db.backends.postgresql.base import DatabaseWrapper as BaseDatabaseWrapper

from authentik.lib.config import CONFIG, reload


class DatabaseWrapper(BaseDatabaseWrapper):
    """database backend which supports rotating credentials"""

    def get_connection_params(self):
        reload()
        conn_params = super().get_connection_params()
        conn_params["user"] = CONFIG.get("postgresql.user")
        conn_params["password"] = CONFIG.get("postgresql.password")
        return conn_params
