"""authentik flow signals"""
from django.core.cache import cache
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.flows.apps import GAUGE_FLOWS_CACHED
from authentik.flows.planner import CACHE_PREFIX
from authentik.root.monitoring import monitoring_set

LOGGER = get_logger()


def delete_cache_prefix(prefix: str) -> int:
    """Delete keys prefixed with `prefix` and return count of deleted keys."""
    keys = cache.keys(prefix)
    cache.delete_many(keys)
    return len(keys)


@receiver(monitoring_set)
def monitoring_set_flows(sender, **kwargs):
    """set flow gauges"""
    GAUGE_FLOWS_CACHED.set(len(cache.keys(f"{CACHE_PREFIX}*") or []))


@receiver(post_save)
@receiver(pre_delete)
def invalidate_flow_cache(sender, instance, **_):
    """Invalidate flow cache when flow is updated"""
    from authentik.flows.models import Flow, FlowStageBinding, Stage
    from authentik.flows.planner import cache_key

    if isinstance(instance, Flow):
        total = delete_cache_prefix(f"{cache_key(instance)}*")
        LOGGER.debug("Invalidating Flow cache", flow=instance, len=total)
    if isinstance(instance, FlowStageBinding):
        total = delete_cache_prefix(f"{cache_key(instance.target)}*")
        LOGGER.debug("Invalidating Flow cache from FlowStageBinding", binding=instance, len=total)
    if isinstance(instance, Stage):
        total = 0
        for binding in FlowStageBinding.objects.filter(stage=instance):
            prefix = cache_key(binding.target)
            total += delete_cache_prefix(f"{prefix}*")
        LOGGER.debug("Invalidating Flow cache from Stage", stage=instance, len=total)
