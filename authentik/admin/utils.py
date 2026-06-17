from authentik.admin.models import SystemSettings


def get_system_settings() -> SystemSettings:
    return SystemSettings.objects.get(pk=True)
