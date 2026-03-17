import base64
import pickle  # nosec
from datetime import UTC, datetime
from typing import Any

from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.cache.backends.db import DatabaseCache as BaseDatabaseCache
from django.db import DatabaseError
from django.db.utils import ProgrammingError
from django.utils.module_loading import import_string
from django.utils.timezone import now
from psqlextra.types import ConflictAction

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

    def _base_set_expiry(self, timeout: float | None) -> datetime:
        timeout = self.get_backend_timeout(timeout)
        if timeout is None:
            exp = datetime.max
        else:
            tz = UTC if settings.USE_TZ else None
            exp = datetime.fromtimestamp(timeout, tz=tz)
        exp.replace(microsecond=0)
        return exp

    def _base_set_data(
        self,
        key: Any,
        value: Any,
        timeout: float | None,
        version: int | None = None,
    ) -> tuple[str, str, datetime]:
        key = self.make_and_validate_key(key, version=version)
        pickled = pickle.dumps(value, self.pickle_protocol)
        # The DB column is expecting a string, so make sure the value is a
        # string, not bytes. Refs #19274.
        b64encoded = base64.b64encode(pickled).decode("latin1")

        return (key, b64encoded, self._base_set_expiry(timeout))

    def touch(
        self,
        key: Any,
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> bool:
        key = self.make_and_validate_key(key, version=version)
        expiry = self._base_set_expiry(timeout)
        try:
            count = CacheEntry.objects.filter(cache_key=key).update(expires=expiry)
            return bool(count != 0)
        except DatabaseError:
            return False

    def add(
        self,
        key: Any,
        value: Any,
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> bool:
        key, value, expiry = self._base_set_data(key, value, timeout, version)
        try:
            CacheEntry.objects.on_conflict(
                ["cache_key"],
                ConflictAction.UPDATE,
                update_values=dict(
                    expires=expiry,
                ),
            ).insert(
                cache_key=key,
                value=value,
                expires=expiry,
            )
            # We don't know if the row already existed, we just return True for success
            return True
        except DatabaseError:
            return False

    def set(
        self,
        key: Any,
        value: Any,
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> None:
        key, value, expiry = self._base_set_data(key, value, timeout, version)
        CacheEntry.objects.on_conflict(
            ["cache_key"],
            ConflictAction.UPDATE,
        ).insert(
            cache_key=key,
            value=value,
            expires=expiry,
        )

    def clear(self) -> None:
        CacheEntry.objects.truncate()
