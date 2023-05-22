"""Enterprise signals"""
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import datetime

from authentik.api.v3.config import Capabilities, capabilities
from authentik.enterprise.models import License


@receiver(capabilities)
def enterprise_capabilities(sender, **_):
    # TODO: Filter not expired
    for license in License.objects.all():
        if license.is_valid():
            return Capabilities.IS_ENTERPRISE_LICENSED
    return None


@receiver(pre_save, sender=License)
def pre_save_license(sender: type[License], instance: License, **_):
    status = instance.status
    instance.name = status.name
    instance.users = status.users
    instance.external_users = status.external_users
    instance.expiry = datetime.fromtimestamp(status.exp)
