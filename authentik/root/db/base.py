"""authentik database backend"""
from authentik.lib.config import CONFIG
from django_prometheus.db.backends.postgresql.base import DatabaseWrapper as BaseDatabaseWrapper


class DatabaseWrapper(BaseDatabaseWrapper):
    """database backend which supports rotating credentials"""

    def get_new_connection(self, *args, **kwargs):
        return super().get_new_connection(*args, **kwargs)

    def get_connection_params(self):
        conn_params = super().get_connection_params()
        conn_params['user'] = CONFIG.y("postgresql.user")
        conn_params['password'] = CONFIG.y("postgresql.password")
        return conn_params
