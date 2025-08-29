"""Enterprise signals"""

from datetime import datetime

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils.timezone import get_current_timezone

from authentik.enterprise.license import CACHE_KEY_ENTERPRISE_LICENSE
from authentik.enterprise.models import License
from authentik.enterprise.tasks import enterprise_update_usage
from authentik.tasks.schedules.models import Schedule


@receiver(pre_save, sender=License)
def pre_save_license(sender: type[License], instance: License, **_):
    """Extract data from license jwt and save it into model"""
    status = instance.status
    instance.name = status.name
    instance.internal_users = status.internal_users
    instance.external_users = status.external_users
    instance.expiry = datetime.fromtimestamp(status.exp, tz=get_current_timezone())


@receiver(post_save, sender=License)
def post_save_license(sender: type[License], instance: License, **_):
    """Trigger license usage calculation when license is saved"""
    cache.delete(CACHE_KEY_ENTERPRISE_LICENSE)
    Schedule.dispatch_by_actor(enterprise_update_usage)


@receiver(post_delete, sender=License)
def post_delete_license(sender: type[License], instance: License, **_):
    """Clear license cache when license is deleted"""
    cache.delete(CACHE_KEY_ENTERPRISE_LICENSE)
