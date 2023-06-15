"""Enterprise signals"""
from datetime import datetime

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import get_current_timezone

from authentik.api.v3.config import Capabilities, capabilities
from authentik.enterprise.models import License, LicenseKey


@receiver(capabilities)
def enterprise_capabilities(sender, **_):
    """Add enterprise licensed capability when license is fully valid"""
    if LicenseKey.get_total().is_valid():
        return Capabilities.IS_ENTERPRISE_LICENSED
    return None


@receiver(pre_save, sender=License)
def pre_save_license(sender: type[License], instance: License, **_):
    """Extract data from license jwt and save it into model"""
    status = instance.status
    instance.name = status.name
    instance.users = status.users
    instance.external_users = status.external_users
    instance.expiry = datetime.fromtimestamp(status.exp, tz=get_current_timezone())
