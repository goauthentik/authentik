from django.dispatch import receiver

from authentik.admin.tasks import _set_prom_info
from authentik.root.signals import post_startup


@receiver(post_startup)
def post_startup_admin_metrics(sender, **_):
    _set_prom_info()
