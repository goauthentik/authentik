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
    from passbook.policies.models import Policy, PolicyBinding
    from passbook.policies.process import cache_key

    if isinstance(instance, Policy):
        LOGGER.debug("Invalidating policy cache", policy=instance)
        total = 0
        for binding in PolicyBinding.objects.filter(policy=instance):
            prefix = f"policy_{binding.policy_binding_uuid.hex}_{binding.policy.pk.hex}" + "*"
            keys = cache.keys(prefix)
            total += len(keys)
            cache.delete_many(keys)
        LOGGER.debug("Deleted keys", len=total)
