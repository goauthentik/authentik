import base64
from collections.abc import Iterable
import pickle  # nosec
from datetime import UTC, datetime
from typing import Any

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT, BaseCache
from django.db import DatabaseError
from django.utils.module_loading import import_string
from django.utils.timezone import now
from psqlextra.types import ConflictAction

from django_postgres_cache.models import CacheEntry


class DatabaseCache(BaseCache):
    pickle_protocol = pickle.HIGHEST_PROTOCOL

    def __init__(self, params: dict[str, Any]) -> None:
        super().__init__(params)
        self.reverse_key_func = import_string(params["REVERSE_KEY_FUNCTION"])

    def _make_value(self, value: Any) -> str:
        pickled = pickle.dumps(value, self.pickle_protocol)
        # The DB column is expecting a string, so make sure the value is a
        # string, not bytes. Refs #19274.
        b64encoded = base64.b64encode(pickled).decode("latin1")

        return b64encoded

    def _unmake_value(self, encoded_value: str) -> Any:
        return pickle.loads(base64.b64decode(encoded_value.encode()))

    def _make_expiry(self, timeout: float | None) -> datetime:
        timeout = self.get_backend_timeout(timeout)
        if timeout is None:
            exp = datetime.max
        else:
            tz = UTC if settings.USE_TZ else None
            exp = datetime.fromtimestamp(timeout, tz=tz)
        exp.replace(microsecond=0)
        return exp

    def add(
        self,
        key: Any,
        value: Any,
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> bool:
        key = self.make_and_validate_key(key, version=version)
        value = self._make_value(value)
        expiry = self._make_expiry(timeout)
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

    def get(self, key: Any, default: Any | None = None, version: int | None = None) -> Any:
        key = self.make_and_validate_key(key, version=version)
        entry = CacheEntry.objects.filter(cache_key=key, expires__gte=now()).first()
        if entry is None:
            return default
        return self._unmake_value(entry.value)

    def set(
        self,
        key: Any,
        value: Any,
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> None:
        key = self.make_and_validate_key(key, version=version)
        value = self._make_value(value)
        expiry = self._make_expiry(timeout)
        CacheEntry.objects.on_conflict(
            ["cache_key"],
            ConflictAction.UPDATE,
        ).insert(
            cache_key=key,
            value=value,
            expires=expiry,
        )

    def touch(
        self,
        key: Any,
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> bool:
        key = self.make_and_validate_key(key, version=version)
        expiry = self._make_expiry(timeout)
        try:
            count = CacheEntry.objects.filter(cache_key=key).update(expires=expiry)
            return count != 0
        except DatabaseError:
            return False

    def delete(self, key: Any, version: int | None = None) -> bool:
        key = self.make_and_validate_key(key, version=version)
        try:
            count = CacheEntry.objects.filter(cache_key=key).delete()
            return count != 0
        except DatabaseError:
            return False

    def get_many(self, keys: Iterable[Any], version: int | None = None) -> dict[Any, Any]:
        if not keys:
            return {}

        key_map = {self.make_and_validate_key(key, version=version): key for key in keys}
        entries = CacheEntry.objects.filter(cache_key__in=key_map.keys(), expires__gte=now())
        result = {}
        for entry in entries:
            result[key_map.get(entry.cache_key)] = self._unmake_value(entry.value)
        return result

    def get_or_set(
        self,
        key: Any,
        default: Any | None,
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> Any | None:
        if callable(default):
            default = default()
        key = self.make_and_validate_key(key, version=version)
        expiry = self._make_expiry(timeout)
        entry = CacheEntry.objects.on_conflict(
            ["cache_key"],
            ConflictAction.NOTHING,
        ).insert_and_get(
            cache_key=key,
            value=default,
            expires=expiry,
        )
        if entry is None:
            entry = CacheEntry.objects.filter(cache_key=key).first()
        if entry is None:
            return None
        return self._unmake_value(entry.value)

    async def aget_or_set(
        self,
        key: Any,
        default: Any | None,
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> Any | None:
        return await sync_to_async(self.get_or_set, thread_sensitive=True)(
            key,
            default,
            timeout,
            version,
        )

    def has_key(self, key: Any, version: int | None = None) -> bool:
        key = self.make_and_validate_key(key, version=version)
        return CacheEntry.objects.filter(cache_key=key, expires__gte=now()).exists()

    async def ahas_key(self, key: Any, version: int | None = None) -> bool:
        key = self.make_and_validate_key(key, version=version)
        return await CacheEntry.objects.filter(cache_key=key, expires__gte=now()).aexists()

    def set_many(
        self,
        data: dict[Any, Any],
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> list[Any]:
        expiry = self._make_expiry(timeout)
        CacheEntry.objects.on_conflict(
            ["cache_key"],
            ConflictAction.UPDATE,
        ).bulk_insert(
            [
                dict(
                    cache_key=self.make_and_validate_key(key, version=version),
                    value=self._make_value(value),
                    expires=expiry,
                )
                for key, value in data.items()
            ]
        )
        return []

    async def aset_many(
        self,
        data: dict[Any, Any],
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> list[Any]:
        return await sync_to_async(self.set_many, thread_sensitive=True)(
            data,
            timeout,
            version,
        )

    def delete_many(self, keys: Iterable[Any], version: int | None = None):
        CacheEntry.objects.filter(
            cache_key__in=[self.make_and_validate_key(key, version=version) for key in keys]
        ).delete()

    async def adelete_many(self, keys: Iterable[Any], version: int | None = None):
        await CacheEntry.objects.filter(
            cache_key__in=[self.make_and_validate_key(key) for key in keys]
        ).adelete()

    def clear(self) -> None:
        CacheEntry.objects.truncate()

    def ttl(self, key: Any, version: int | None = None) -> int | None:
        key = self.make_and_validate_key(key, version=version)
        entry = CacheEntry.objects.filter(cache_key=key).first()
        if entry is None:
            return None
        return (entry.expires - now()).total_seconds()

    def keys(self, keys_pattern: str, version: int | None = None) -> list[str]:
        keys_pattern = self.make_key(keys_pattern.replace("*", ".*"), version=version)

        return [
            self.reverse_key_func(key)
            for key in CacheEntry.objects.filter(
                cache_key__regex=keys_pattern,
            ).values_list(
                "cache_key",
                flat=True,
            )
        ]
