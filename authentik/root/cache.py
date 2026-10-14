from collections.abc import Callable, Hashable
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from threading import Lock
from time import monotonic
from typing import Any

from django.db import connection


def make_key(key: str, key_prefix: str, version: int) -> str:
    return f"{connection.schema_name}:{key_prefix}:{version}:{key}"


def reverse_key(key: str) -> str:
    return key.split(":", 3)[3]


class in_memory_cache:
    """Cache a function's result in process memory, keyed by `key(*args, **kwargs)`.

    Within `timeout` seconds the cached value is returned as-is. Once stale, the stale
    value is still returned while a single background worker refreshes it.
    The cache is per-process; call `.cache_clear()` on the wrapped function to invalidate."""

    def __init__(self, key: Callable[..., Hashable], timeout: float = 30, maxsize: int = 1024):
        self.key = key
        self.timeout = timeout
        self.maxsize = maxsize
        self._values: dict[Hashable, tuple[float, Any]] = {}
        self._lock = Lock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="in_memory_cache")

    def _store(self, key: Hashable, value: Any):
        # drop everything when full instead of LRU; keys can come from
        # client input (e.g. Host header), so this only needs to bound memory
        if key not in self._values and len(self._values) >= self.maxsize:
            self._values.clear()
        self._values[key] = (monotonic(), value)

    def __call__(self, func: Callable) -> Callable:
        def refresh(key: Hashable, args: tuple, kwargs: dict):
            # Another thread is already refreshing; the next stale read will retry
            if not self._lock.acquire(blocking=False):
                return
            try:
                # Skip if a refresh finished between the stale read and acquiring the lock
                cached = self._values.get(key)
                if cached is None or monotonic() - cached[0] > self.timeout:
                    self._store(key, func(*args, **kwargs))
            finally:
                self._lock.release()
                # The worker thread has its own DB connection, which Django won't close
                connection.close()

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = self.key(*args, **kwargs)
            cached = self._values.get(key)
            if cached is None:
                value = func(*args, **kwargs)
                self._store(key, value)
                return value
            stored_at, value = cached
            if monotonic() - stored_at > self.timeout and not self._lock.locked():
                self._executor.submit(refresh, key, args, kwargs)
            return value

        wrapper.cache_clear = self._values.clear  # type: ignore[attr-defined]
        return wrapper
