"""authentik brand signals"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from authentik.brands.models import Brand
from authentik.brands.utils import get_brand_for_request
from authentik.core.models import Application
from authentik.flows.models import Flow


@receiver(post_save, sender=Brand)
@receiver(post_delete, sender=Brand)
# Cached brands carry their flows and default application (see _BRAND_RELATED_FK_FIELDS)
@receiver(post_save, sender=Flow)
@receiver(post_delete, sender=Flow)
@receiver(post_save, sender=Application)
@receiver(post_delete, sender=Application)
def brand_cache_clear(**_):
    """Drop cached brand lookups when a brand or an object it caches changes"""
    get_brand_for_request.invalidate()
