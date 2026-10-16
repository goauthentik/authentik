"""authentik admin utils"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from authentik.admin.models import SystemSettings

_CTX_SYSTEM_SETTINGS = ContextVar[dict[str, SystemSettings] | None](
    "authentik_system_settings", default=None
)


def get_system_settings() -> SystemSettings:
    cache = _CTX_SYSTEM_SETTINGS.get()
    if cache is None:
        return SystemSettings.objects.get(pk=True)
    if "settings" not in cache:
        cache["settings"] = SystemSettings.objects.get(pk=True)
    return cache["settings"]


@contextmanager
def system_settings_cache() -> Iterator[None]:
    token = _CTX_SYSTEM_SETTINGS.set({})
    try:
        yield
    finally:
        _CTX_SYSTEM_SETTINGS.reset(token)


def clear_system_settings_cache() -> None:
    if (cache := _CTX_SYSTEM_SETTINGS.get()) is not None:
        cache.clear()


def normalize_base_url(value: str | None) -> str:
    """Normalize a configured base URL: strip whitespace and trailing slashes."""
    return (value or "").strip().rstrip("/")
