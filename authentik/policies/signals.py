"""authentik policy signals"""
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.core.api.applications import user_app_cache_key
from authentik.policies.apps import GAUGE_POLICIES_CACHED
from authentik.policies.types import CACHE_PREFIX
from authentik.root.monitoring import monitoring_set

LOGGER = get_logger()


@receiver(monitoring_set)
def monitoring_set_policies(sender, **kwargs):
    """set policy gauges"""
    GAUGE_POLICIES_CACHED.set(len(cache.keys(f"{CACHE_PREFIX}_*") or []))


@receiver(post_save)
def invalidate_policy_cache(sender, instance, **_):
    """Invalidate Policy cache when policy is updated"""
    from authentik.policies.models import Policy, PolicyBinding

    if isinstance(instance, Policy):
        total = 0
        for binding in PolicyBinding.objects.filter(policy=instance):
            prefix = f"{CACHE_PREFIX}{binding.policy_binding_uuid.hex}_{binding.policy.pk.hex}*"
            keys = cache.keys(prefix)
            total += len(keys)
            cache.delete_many(keys)
        LOGGER.debug("Invalidating policy cache", policy=instance, keys=total)
    # Also delete user application cache
    keys = cache.keys(user_app_cache_key("*")) or []
    cache.delete_many(keys)
