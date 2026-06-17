from authentik.admin.models import SystemSettings
from authentik.root.install_id import get_install_id


def get_system_settings() -> SystemSettings:
    try:
        return SystemSettings.objects.get(pk=True)
    except SystemSettings.DoesNotExist:
        return SystemSettings(pk=False)


def get_unique_identifier() -> str:
    """Get a globally unique identifier that does not change"""
    return get_install_id()
