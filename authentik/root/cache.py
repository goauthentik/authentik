from collections.abc import Callable, Hashable
from functools import wraps
from time import monotonic
from typing import Any, Protocol, cast

from django.db import connection
from django.db.models import Model


def make_key(key: str, key_prefix: str, version: int) -> str:
    return f"{connection.schema_name}:{key_prefix}:{version}:{key}"


def reverse_key(key: str) -> str:
    return key.split(":", 3)[3]


def models_version(*models: type[Model]) -> tuple[Any, ...]:
    """Cheap fingerprint of whole tables, which changes when any row is created, updated
    or deleted. Requires a `last_updated` field (see `CreatedUpdatedModel`).

    Sums the timestamps instead of taking their max, as an update written by a server
    whose clock is slightly behind could otherwise leave the max unchanged."""
    selects = ", ".join(
        f"(SELECT sum(extract(epoch FROM last_updated)) FROM {connection.ops.quote_name(table)})"
        for table in (model._meta.db_table for model in models)
    )
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT {selects}")  # nosec
        return tuple(cursor.fetchone() or ())


class CachedFunction[**P, R](Protocol):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...

    def cache_clear(self) -> None: ...


class in_memory_cache:
    """Cache a function's result in process memory, keyed by `key(*args, **kwargs)`.

    Within `timeout` seconds the cached value is returned as-is. After that, the cheap
    `version()` is compared to the one stored with the value, and the function is only
    called again when it changed.
    The cache is per-process; call `.cache_clear()` on the wrapped function to invalidate."""

    def __init__(
        self,
        key: Callable[..., Hashable],
        version: Callable[[], Hashable],
        timeout: float = 30,
        maxsize: int = 1024,
    ):
        self.key = key
        self.version = version
        self.timeout = timeout
        self.maxsize = maxsize
        self._values: dict[Hashable, tuple[float, Hashable, Any]] = {}

    def _store(self, key: Hashable, version: Hashable, value: Any) -> None:
        # drop everything when full instead of LRU; keys can come from
        # client input (e.g. Host header), so this only needs to bound memory
        if key not in self._values and len(self._values) >= self.maxsize:
            self._values.clear()
        self._values[key] = (monotonic(), version, value)

    def __call__[**P, R](self, func: Callable[P, R]) -> CachedFunction[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = self.key(*args, **kwargs)
            cached = self._values.get(key)
            if cached is not None and monotonic() - cached[0] <= self.timeout:
                return cast(R, cached[2])
            # Read the version first: a change committed in between makes the next
            # check refetch, instead of storing an old value under a new version
            version = self.version()
            if cached is not None and cached[1] == version:
                value = cast(R, cached[2])
            else:
                value = func(*args, **kwargs)
            self._store(key, version, value)
            return value

        wrapper.cache_clear = self._values.clear  # type: ignore[attr-defined]
        return cast(CachedFunction[P, R], wrapper)
