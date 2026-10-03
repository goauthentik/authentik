from django.db.models.signals import post_save
from django.dispatch import Signal, receiver

from authentik.admin.models import SystemSettings
from authentik.admin.tasks import _set_prom_info
from authentik.admin.utils import clear_system_settings_cache
from authentik.root.signals import post_startup

flag_set = Signal()


@receiver(post_startup)
def post_startup_admin_metrics(sender, **_):
    _set_prom_info()


@receiver(post_save, sender=SystemSettings)
def system_settings_saved(**_):
    clear_system_settings_cache()
