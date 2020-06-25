"""passbook flow signals"""
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from structlog import get_logger

LOGGER = get_logger()


@receiver(post_save)
# pylint: disable=unused-argument
def invalidate_flow_cache(sender, instance, **_):
    """Invalidate flow cache when flow is updated"""
    from passbook.flows.models import Flow, FlowStageBinding, Stage
    from passbook.flows.planner import cache_key

    if isinstance(instance, Flow):
        LOGGER.debug("Invalidating Flow cache", flow=instance)
        cache.delete(f"{cache_key(instance)}*")
    if isinstance(instance, FlowStageBinding):
        LOGGER.debug("Invalidating Flow cache from FlowStageBinding", binding=instance)
        cache.delete(f"{cache_key(instance.flow)}*")
    if isinstance(instance, Stage):
        LOGGER.debug("Invalidating Flow cache from Stage", stage=instance)
        total = 0
        for binding in FlowStageBinding.objects.filter(stage=instance):
            prefix = cache_key(binding.flow)
            keys = cache.keys(f"{prefix}*")
            total += len(keys)
            cache.delete_many(keys)
        LOGGER.debug("Deleted keys", len=total)
