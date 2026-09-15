"""authentik admin utils"""

from authentik.admin.models import SystemSettings


def get_system_settings(only: list[str] | None = None) -> SystemSettings:
    """Get the system settings for this instance"""
    qs = SystemSettings.objects
    if only:
        qs = qs.only(*only)
    return qs.get(pk=True)


def normalize_base_url(value: str | None) -> str:
    """Normalize a configured base URL: strip whitespace and trailing slashes."""
    return (value or "").strip().rstrip("/")
