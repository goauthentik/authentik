"""passbook policy signals"""
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from structlog import get_logger

LOGGER = get_logger()


@receiver(post_save)
# pylint: disable=unused-argument
def invalidate_policy_cache(sender, instance, **_):
    """Invalidate Policy cache when policy is updated"""
    from passbook.policies.models import Policy

    if isinstance(instance, Policy):
        LOGGER.debug("Invalidating policy cache", policy=instance)
        prefix = f"policy_{instance.pk}_*"
        keys = cache.keys(prefix)
        cache.delete_many(keys)
        LOGGER.debug("Deleted %d keys", len(keys))
