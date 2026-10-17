from asyncio import Task, create_task, get_running_loop, sleep
from collections.abc import Callable, Hashable
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from os import getpid
from threading import Lock
from time import monotonic
from typing import Any, ClassVar, Protocol, cast

from channels.layers import get_channel_layer
from django.conf import settings
from django.db import connection, transaction
from structlog.stdlib import get_logger

LOGGER = get_logger()
INVALIDATION_GROUP = "authentik_in_memory_cache"


def make_key(key: str, key_prefix: str, version: int) -> str:
    return f"{connection.schema_name}:{key_prefix}:{version}:{key}"


def reverse_key(key: str) -> str:
    return key.split(":", 3)[3]


class CachedFunction[**P, R](Protocol):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...

    def cache_clear(self) -> None: ...

    def invalidate(self) -> None: ...


_listener: tuple[int, Task[None]] | None = None


def start_invalidation_listener() -> None:
    """Clear caches when another process invalidates them. Runs as a task on the server's
    event loop, so it shares that loop's channel layer connections"""
    global _listener  # noqa: PLW0603
    # Checked against the PID so forked workers start their own listener
    if settings.TEST or (_listener and _listener[0] == getpid()):
        return
    # Keep a reference, otherwise the task can be garbage collected
    _listener = (getpid(), get_running_loop().create_task(_listen()))


async def _join_group(layer: Any, channel: str) -> None:
    # Group membership expires, re-join well before it does
    while True:
        try:
            await layer.group_add(INVALIDATION_GROUP, channel)
            await sleep(layer.group_expiry / 2)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Failed to join cache invalidation group", exc=exc)
            await sleep(5)


async def _listen() -> None:
    layer = get_channel_layer()
    channel = await layer.new_channel()
    join = create_task(_join_group(layer, channel))  # noqa: F841
    while True:
        try:
            message = await layer.receive(channel)
            if cache := in_memory_cache.registry.get(message.get("name", "")):
                cache._values.clear()
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Failed to receive cache invalidation", exc=exc)
            await sleep(5)


class in_memory_cache:
    """Cache a function's result in process memory, keyed by `key(*args, **kwargs)`.

    Within `timeout` seconds the cached value is returned as-is. Once stale, the stale
    value is still returned while a single background worker refreshes it.
    The cache is per-process: `.invalidate()` on the wrapped function clears it in every
    process via the channel layer, `.cache_clear()` only in the current one."""

    registry: ClassVar[dict[str, in_memory_cache]] = {}

    def __init__(self, key: Callable[..., Hashable], timeout: float = 30, maxsize: int = 1024):
        self.key = key
        self.timeout = timeout
        self.maxsize = maxsize
        self._values: dict[Hashable, tuple[float, Any]] = {}
        self._lock = Lock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="in_memory_cache")

    def _store(self, key: Hashable, value: Any) -> None:
        # drop everything when full instead of LRU; keys can come from
        # client input (e.g. Host header), so this only needs to bound memory
        if key not in self._values and len(self._values) >= self.maxsize:
            self._values.clear()
        self._values[key] = (monotonic(), value)

    def __call__[**P, R](self, func: Callable[P, R]) -> CachedFunction[P, R]:
        name = f"{func.__module__}.{func.__qualname__}"
        in_memory_cache.registry[name] = self

        def refresh(key: Hashable, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
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
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = self.key(*args, **kwargs)
            cached = self._values.get(key)
            if cached is None:
                value = func(*args, **kwargs)
                self._store(key, value)
                return value
            stored_at, value = cached
            if monotonic() - stored_at > self.timeout and not self._lock.locked():
                self._executor.submit(refresh, key, args, kwargs)
            return cast(R, value)

        def invalidate() -> None:
            self._values.clear()
            # Other processes would re-read the old row before the change is committed
            transaction.on_commit(
                lambda: get_channel_layer().group_send_blocking(
                    INVALIDATION_GROUP, {"type": "cache.invalidate", "name": name}
                )
            )

        wrapper.cache_clear = self._values.clear  # type: ignore[attr-defined]
        wrapper.invalidate = invalidate  # type: ignore[attr-defined]
        return cast(CachedFunction[P, R], wrapper)
