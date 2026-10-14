"""authentik brand signals"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from authentik.brands.models import Brand
from authentik.brands.utils import get_brand_for_request


@receiver(post_save, sender=Brand)
@receiver(post_delete, sender=Brand)
def brand_cache_clear(**_):
    """Drop cached brand lookups when any brand changes"""
    get_brand_for_request.cache_clear()
