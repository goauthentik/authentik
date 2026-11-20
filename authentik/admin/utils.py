"""authentik admin utils"""

from authentik.admin.models import SystemSettings
from authentik.lib.config import CONFIG
from authentik.root.cache import in_memory_cache


@in_memory_cache(key=lambda: None, timeout=CONFIG.get_int("cache.timeout_system_settings", 30))
def get_system_settings() -> SystemSettings:
    """Get the system settings. The returned object is shared, don't mutate it."""
    return SystemSettings.objects.get(pk=True)


def normalize_base_url(value: str | None) -> str:
    """Normalize a configured base URL: strip whitespace and trailing slashes."""
    return (value or "").strip().rstrip("/")
