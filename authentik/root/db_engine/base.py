"""Database engine that uses prometheus exporter"""
from django.db.backends.postgresql import base
from django_prometheus.db.common import DatabaseWrapperMixin, ExportingCursorWrapper


class DatabaseFeatures(base.DatabaseFeatures):
    """Our database has the exact same features as the base one."""


class DatabaseWrapper(DatabaseWrapperMixin, base.DatabaseWrapper):
    """Database wrapper which exports metrics to prometheus"""

    def get_connection_params(self):
        conn_params = super().get_connection_params()
        conn_params["cursor_factory"] = ExportingCursorWrapper(base.Cursor, self.alias, self.vendor)
        return conn_params

    def create_cursor(self, name=None):
        # cursor_factory is a kwarg to connect() so restore create_cursor()'s
        # default behavior
        return base.DatabaseWrapper.create_cursor(self, name=name)
