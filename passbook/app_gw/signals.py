"""passbook app_gw cache clean signals"""

from logging import getLogger

from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from passbook.app_gw.models import ApplicationGatewayProvider
from passbook.app_gw.proxy.handler import IGNORED_HOSTNAMES_KEY

LOGGER = getLogger(__name__)

@receiver(post_save)
# pylint: disable=unused-argument
def invalidate_app_gw_cache(sender, instance, **kwargs):
    """Invalidate Policy cache when app_gw is updated"""
    if isinstance(instance, ApplicationGatewayProvider):
        LOGGER.debug("Invalidating cache for ignored hostnames")
        cache.delete(IGNORED_HOSTNAMES_KEY)
