from typing import Any

from channels_postgres.core import PostgresChannelLayer as BasePostgresChannelLayer
from channels_postgres.db import DatabaseLayer as BaseDatabaseLayer
from django.conf import settings
from psycopg_pool import AsyncConnectionPool

from authentik.root.db.base import DatabaseWrapper


class DatabaseLayer(BaseDatabaseLayer):
    async def get_db_pool(self, db_params: dict[str, Any]) -> AsyncConnectionPool:
        db_wrapper = DatabaseWrapper(settings.CHANNEL_LAYERS["default"]["CONFIG"])
        db_params = db_wrapper.get_connection_params()
        db_params.pop("cursor_factory")
        db_params.pop("context")
        return await super().get_db_pool(db_params)


class PostgresChannelLayer(BasePostgresChannelLayer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.django_db = DatabaseLayer(self.django_db.psycopg_options, self.db_params)

    @property
    def db_params(self):
        db_wrapper = DatabaseWrapper(settings.CHANNEL_LAYERS["default"]["CONFIG"])
        db_params = db_wrapper.get_connection_params()
        db_params.pop("cursor_factory")
        db_params.pop("context")
        return db_params

    @db_params.setter
    def db_params(self, value):
        pass
