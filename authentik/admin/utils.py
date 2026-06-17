from authentik.admin.models import SystemSettings


def get_system_settings() -> SystemSettings:
    try:
        return SystemSettings.objects.get(pk=True)
    except SystemSettings.DoesNotExist:
        return SystemSettings(pk=False)
