import base64
import pickle  # nosec
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT, BaseCache, get_key_func
from django.db import DatabaseError
from django.utils.timezone import now
from psqlextra.types import ConflictAction

from django_postgres_cache.models import CacheEntry


class DatabaseCache(BaseCache):
    pickle_protocol = pickle.HIGHEST_PROTOCOL

    def __init__(self, location: Any, params: dict[str, Any]) -> None:
        super().__init__(params)
        self.reverse_key_func = get_key_func(params["REVERSE_KEY_FUNCTION"])

    def _make_value(self, value: Any) -> str:
        pickled = pickle.dumps(value, self.pickle_protocol)
        # The DB column is expecting a string, so make sure the value is a
        # string, not bytes. Refs #19274.
        b64encoded = base64.b64encode(pickled).decode("latin1")

        return b64encoded

    def _unmake_value(self, encoded_value: str) -> Any:
        return pickle.loads(base64.b64decode(encoded_value.encode()))  # nosec

    def _make_expiry(self, timeout: float | None) -> datetime:
        timeout = self.get_backend_timeout(timeout)
        if timeout is None:
            exp = datetime.max
        else:
            tz = UTC if settings.USE_TZ else None
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
        value = self._make_value(value)
        expiry = self._make_expiry(timeout)
        # No need for a transaction here, since old values get deleted
        CacheEntry.objects.filter(cache_key=key, expires__lte=now()).delete()
        try:
            CacheEntry.objects.create(cache_key=key, value=value, expires=expiry)
            return True
        except DatabaseError:
            # Any error, including integrity error and we didn't insert the row
            return False

    def get(self, key: Any, default: Any | None = None, version: int | None = None) -> Any:
        key = self.make_and_validate_key(key, version=version)
        try:
            entry = CacheEntry.objects.filter(cache_key=key, expires__gte=now()).first()
        except DatabaseError:
            entry = None
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
        return bool(CacheEntry.objects.filter(cache_key=key).update(expires=expiry))

    def delete(self, key: Any, version: int | None = None) -> bool:
        key = self.make_and_validate_key(key, version=version)
        count, _ = CacheEntry.objects.filter(cache_key=key).delete()
        return bool(count)

    def get_many(self, keys: Iterable[Any], version: int | None = None) -> dict[Any, Any]:
        key_map = {self.make_and_validate_key(key, version=version): key for key in keys}
        entries = CacheEntry.objects.filter(cache_key__in=key_map.keys(), expires__gte=now())
        result = {}
        for entry in entries:
            result[key_map[entry.cache_key]] = self._unmake_value(entry.value)
        return result

    def get_or_set(
        self,
        key: Any,
        default: Any | None,
        timeout: float | None = DEFAULT_TIMEOUT,
        version: int | None = None,
    ) -> Any | None:
        key = self.make_and_validate_key(key, version=version)
        if callable(default):
            default = default()
        default = self._make_value(default)
        expiry = self._make_expiry(timeout)
        entry = CacheEntry.objects.on_conflict(
            ["cache_key"],
            ConflictAction.NOTHING,
        ).insert_and_get(
            cache_key=key,
            value=default,
            expires=expiry,
        )
        # If the row already existed, nothing is returned
        if entry is None:
            entry = CacheEntry.objects.filter(cache_key=key).first()
        # Sanity check, should not happen
        if entry is None:
            return None
        return self._unmake_value(entry.value)

    def has_key(self, key: Any, version: int | None = None) -> bool:
        key = self.make_and_validate_key(key, version=version)
        return bool(CacheEntry.objects.filter(cache_key=key, expires__gte=now()).exists())

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

    def delete_many(self, keys: Iterable[Any], version: int | None = None) -> None:
        CacheEntry.objects.filter(
            cache_key__in=[self.make_and_validate_key(key, version=version) for key in keys]
        ).delete()

    def clear(self) -> None:
        CacheEntry.objects.truncate()

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
