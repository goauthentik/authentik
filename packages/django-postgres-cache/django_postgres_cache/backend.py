import base64
import pickle  # nosec
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT, BaseCache, get_key_func
from django.db import DatabaseError, connections, router
from django.db.backends.utils import CursorWrapper
from django.utils.timezone import now

from django_postgres_cache.models import CacheEntry


def default_reverse_key_func(key: str) -> str:
    """Inverse of django.core.cache.backends.base.default_key_func"""
    return key.split(":", 2)[2]


class DatabaseCache(BaseCache):
    pickle_protocol = pickle.HIGHEST_PROTOCOL

    def __init__(self, location: Any, params: dict[str, Any]) -> None:
        super().__init__(params)
        reverse_key_function = params.get("REVERSE_KEY_FUNCTION")
        self.reverse_key_func = (
            get_key_func(reverse_key_function) if reverse_key_function else default_reverse_key_func
        )

    def _cursor(self, write: bool = False) -> CursorWrapper:
        # Raw SQL instead of the ORM: cache calls are on nearly every request, and
        # compiling the equivalent queryset costs more CPU than the query itself
        alias = router.db_for_write(CacheEntry) if write else router.db_for_read(CacheEntry)
        return connections[alias].cursor()

    def _make_value(self, value: Any) -> str:
        pickled = pickle.dumps(value, self.pickle_protocol)
        # The DB column is expecting a string, so make sure the value is a
        # string, not bytes. Refs #19274.
        b64encoded = base64.b64encode(pickled).decode("latin1")

        return b64encoded

    def _unmake_value(self, encoded_value: str) -> Any:
        return pickle.loads(base64.b64decode(encoded_value.encode()))  # nosec

    def _make_expiry(self, timeout: float | None) -> datetime:
        tz = UTC if settings.USE_TZ else None
        timeout = self.get_backend_timeout(timeout)
        if timeout is None:
            exp = datetime.max.replace(tzinfo=tz)
        else:
            exp = datetime.fromtimestamp(timeout, tz=tz)
        exp = exp.replace(microsecond=0)
        return exp

    def add(
        self,
        key: Any,
        value: Any,
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> bool:
        key = self.make_and_validate_key(key, version=version)
        try:
            with self._cursor(write=True) as cursor:
                # Only replaces an existing row if it has expired
                cursor.execute(
                    "INSERT INTO django_postgres_cache_cacheentry AS entry "
                    "(cache_key, value, expires) "
                    "VALUES (%s, %s, %s) ON CONFLICT (cache_key) "
                    "DO UPDATE SET value = EXCLUDED.value, expires = EXCLUDED.expires "
                    "WHERE entry.expires < %s",
                    [key, self._make_value(value), self._make_expiry(timeout), now()],
                )
                return bool(cursor.rowcount)
        except DatabaseError:
            return False

    def get(self, key: Any, default: Any | None = None, version: int | None = None) -> Any:
        key = self.make_and_validate_key(key, version=version)
        try:
            with self._cursor() as cursor:
                cursor.execute(
                    "SELECT value FROM django_postgres_cache_cacheentry "
                    "WHERE cache_key = %s AND expires >= %s",
                    [key, now()],
                )
                row = cursor.fetchone()
        except DatabaseError:
            row = None
        if row is None:
            return default
        return self._unmake_value(row[0])

    def set(
        self,
        key: Any,
        value: Any,
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> None:
        key = self.make_and_validate_key(key, version=version)
        with self._cursor(write=True) as cursor:
            cursor.execute(
                "INSERT INTO django_postgres_cache_cacheentry (cache_key, value, expires) "
                "VALUES (%s, %s, %s) "
                "ON CONFLICT (cache_key) "
                "DO UPDATE SET value = EXCLUDED.value, expires = EXCLUDED.expires",
                [key, self._make_value(value), self._make_expiry(timeout)],
            )

    def touch(
        self,
        key: Any,
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> bool:
        key = self.make_and_validate_key(key, version=version)
        with self._cursor(write=True) as cursor:
            cursor.execute(
                "UPDATE django_postgres_cache_cacheentry SET expires = %s WHERE cache_key = %s",
                [self._make_expiry(timeout), key],
            )
            return bool(cursor.rowcount)

    def delete(self, key: Any, version: int | None = None) -> bool:
        key = self.make_and_validate_key(key, version=version)
        with self._cursor(write=True) as cursor:
            cursor.execute(
                "DELETE FROM django_postgres_cache_cacheentry WHERE cache_key = %s", [key]
            )
            return bool(cursor.rowcount)

    def get_many(self, keys: Iterable[Any], version: int | None = None) -> dict[Any, Any]:
        key_map = {self.make_and_validate_key(key, version=version): key for key in keys}
        if not key_map:
            return {}
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT cache_key, value FROM django_postgres_cache_cacheentry "
                "WHERE cache_key = ANY(%s) AND expires >= %s",
                [list(key_map), now()],
            )
            rows = cursor.fetchall()
        return {key_map[key]: self._unmake_value(value) for key, value in rows}

    def has_key(self, key: Any, version: int | None = None) -> bool:
        key = self.make_and_validate_key(key, version=version)
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM django_postgres_cache_cacheentry "
                "WHERE cache_key = %s AND expires >= %s",
                [key, now()],
            )
            return cursor.fetchone() is not None

    def set_many(
        self,
        data: dict[Any, Any],
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> list[Any]:
        if not data:
            return []
        expiry = self._make_expiry(timeout)
        with self._cursor(write=True) as cursor:
            cursor.executemany(
                "INSERT INTO django_postgres_cache_cacheentry (cache_key, value, expires) "
                "VALUES (%s, %s, %s) "
                "ON CONFLICT (cache_key) "
                "DO UPDATE SET value = EXCLUDED.value, expires = EXCLUDED.expires",
                [
                    [
                        self.make_and_validate_key(key, version=version),
                        self._make_value(value),
                        expiry,
                    ]
                    for key, value in data.items()
                ],
            )
        return []

    def delete_many(self, keys: Iterable[Any], version: int | None = None) -> None:
        keys = [self.make_and_validate_key(key, version=version) for key in keys]
        if not keys:
            return
        with self._cursor(write=True) as cursor:
            cursor.execute(
                "DELETE FROM django_postgres_cache_cacheentry WHERE cache_key = ANY(%s)", [keys]
            )

    def clear(self) -> None:
        CacheEntry.objects.truncate()

    def keys(self, keys_pattern: str, version: int | None = None) -> list[str]:
        """Return cache keys matching a glob pattern (``*`` wildcard).

        Simple ``prefix*`` patterns use Django's ``__startswith`` lookup
        (``LIKE 'prefix%'``), which can be answered by a B-tree index on
        ``cache_key`` and is dramatically cheaper than the regex path even
        without one. No-wildcard patterns reduce to primary-key equality.
        Complex patterns (wildcards in non-suffix position, multiple
        wildcards) fall back to ``__regex``.
        """
        wildcard_count = keys_pattern.count("*")
        if wildcard_count == 0:
            key = self.make_key(keys_pattern, version=version)
            qs = CacheEntry.objects.filter(cache_key=key)
        # This also handles a pattern of "*". The prefix is then "", which will end up as an `all`
        # query, +/- the various prefixes prepended to it.
        elif wildcard_count == 1 and keys_pattern.endswith("*"):
            prefix = self.make_key(keys_pattern[:-1], version=version)
            qs = CacheEntry.objects.filter(cache_key__startswith=prefix)
        else:
            regex = self.make_key(keys_pattern.replace("*", ".*"), version=version)
            qs = CacheEntry.objects.filter(cache_key__regex=regex)

        return [self.reverse_key_func(key) for key in qs.values_list("cache_key", flat=True)]
