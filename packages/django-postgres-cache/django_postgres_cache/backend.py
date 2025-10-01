from typing import Any

from django.core.cache.backends.db import DatabaseCache as BaseDatabaseCache
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
            return default

    def keys(self, keys_pattern: str, version: int | None = None) -> list[str]:
        try:
            return self._keys(keys_pattern, version=version)
        except ProgrammingError:
            return []

    def _keys(self, keys_pattern: str, version: int | None = None) -> list[str]:
        keys_pattern = self.make_key(keys_pattern.replace("*", ".*"), version=version)

        return [
            self.reverse_key_func(key)
            for key in CacheEntry.objects.filter(cache_key__regex=keys_pattern).values_list(
                "cache_key", flat=True
            )
        ]

    def ttl(self, key: str, version: int | None = None) -> int | None:
        """Get TTL left for a given key and version"""
        key = self.make_and_validate_key(key, version=version)
        entry = CacheEntry.objects.filter(cache_key=key).first()
        if not entry:
            return None
        return int((entry.expires - now()).total_seconds())
