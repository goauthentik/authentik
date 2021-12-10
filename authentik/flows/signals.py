"""authentik flow signals"""
from django.core.cache import cache
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from structlog.stdlib import get_logger

LOGGER = get_logger()


@receiver(post_save)
@receiver(pre_delete)
# pylint: disable=unused-argument
def invalidate_flow_cache(sender, instance, **_):
    """Invalidate flow cache when flow is updated"""
    from authentik.flows.models import Flow, FlowStageBinding, Stage
    from authentik.flows.planner import cache_key

    if isinstance(instance, Flow):
        total = cache.delete_pattern(f"{cache_key(instance)}*")
        LOGGER.debug("Invalidating Flow cache", flow=instance, len=total)
    if isinstance(instance, FlowStageBinding):
        total = cache.delete_pattern(f"{cache_key(instance.target)}*")
        LOGGER.debug("Invalidating Flow cache from FlowStageBinding", binding=instance, len=total)
    if isinstance(instance, Stage):
        total = 0
        for binding in FlowStageBinding.objects.filter(stage=instance):
            prefix = cache_key(binding.target)
            total += cache.delete_pattern(f"{prefix}*")
        LOGGER.debug("Invalidating Flow cache from Stage", stage=instance, len=total)
