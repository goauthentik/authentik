from typing import Any

from django.core.cache.backends.db import DatabaseCache as BaseDatabaseCache
from django.db import connections, router
from django.db.utils import ProgrammingError
from django.utils.module_loading import import_string
from django.utils.timezone import now

from django_postgres_cache.models import CacheEntry


class DatabaseCache(BaseDatabaseCache):

    def __init__(self, table: str, params: dict[str, Any]) -> None:
        super().__init__(table, params)
        self.reverse_key_func = import_string(params["REVERSE_KEY_FUNCTION"])
        self._table = CacheEntry._meta.db_table
        self.cache_model_class = CacheEntry

    def _cull(self, *args: Any, **kwargs: Any) -> None:
        """Stubbed out cull method as we cull in a background task"""
        pass

    def get(self, key: str, default: Any | None = None, version: int | None = None) -> Any:
        try:
            return super().get(key, default=default, version=version)
        except ProgrammingError:
            return {}

    def keys(self, keys_pattern: str, version: int | None = None) -> list[str]:
        try:
            return self._keys(keys_pattern, version=version)
        except ProgrammingError:
            return []

    def _keys(self, keys_pattern: str, version: int | None = None) -> list[str]:
        keys_pattern = self.make_key(keys_pattern.replace("*", ".*"), version=version)
        db = router.db_for_read(self.cache_model_class)
        connection = connections[db]
        quote_name = connection.ops.quote_name
        table = quote_name(self._table)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT {} FROM {} WHERE {} ~ {}".format(  # nosec
                    quote_name("cache_key"),
                    table,
                    quote_name("cache_key"),
                    "%s",
                ),
                [keys_pattern],
            )
            rows = cursor.fetchall()

        return [self.reverse_key_func(row[0]) for row in rows]

    def ttl(self, key: str, version: int | None = None) -> int | None:
        """Get TTL left for a given key and version"""
        key = self.make_and_validate_key(key, version=version)
        db = router.db_for_read(self.cache_model_class)
        connection = connections[db]
        quote_name = connection.ops.quote_name
        table = quote_name(self._table)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT {} FROM {} WHERE {} = {}".format(  # nosec
                    quote_name("expires"),
                    table,
                    quote_name("cache_key"),
                    "%s",
                ),
                [key],
            )
            rows = cursor.fetchall()

        if not rows:
            return None
        return int((rows[0].expires - now()).total_seconds())
