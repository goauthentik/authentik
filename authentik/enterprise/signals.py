"""Enterprise signals"""

from datetime import UTC, datetime

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils.timezone import get_current_timezone, now

from authentik.enterprise.apps import GAUGE_LICENSE_EXPIRY, GAUGE_LICENSE_USAGE
from authentik.enterprise.license import CACHE_KEY_ENTERPRISE_LICENSE, LicenseKey
from authentik.enterprise.models import License, LicenseUsageStatus
from authentik.enterprise.tasks import enterprise_update_usage
from authentik.root.monitoring import monitoring_set
from authentik.tasks.schedules.models import Schedule


@receiver(monitoring_set)
def monitoring_set_enterprise(sender, **kwargs):
    """set enterprise gauges"""
    summary = LicenseKey.cached_summary()
    if summary.status == LicenseUsageStatus.UNLICENSED:
        return
    percentage_internal = (
        0
        if summary.internal_users <= 0
        else LicenseKey.get_internal_user_count() / (summary.internal_users / 100)
    )
    percentage_external = (
        0
        if summary.external_users <= 0
        else LicenseKey.get_external_user_count() / (summary.external_users / 100)
    )
    GAUGE_LICENSE_USAGE.labels(user_type="internal").set(percentage_internal)
    GAUGE_LICENSE_USAGE.labels(user_type="external").set(percentage_external)
    GAUGE_LICENSE_EXPIRY.set((summary.latest_valid.replace(tzinfo=UTC) - now()).total_seconds())


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
