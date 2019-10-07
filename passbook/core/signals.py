"""passbook core signals"""
from django.core.cache import cache
from django.core.signals import Signal
from django.db.models.signals import post_save
from django.dispatch import receiver
from structlog import get_logger

LOGGER = get_logger()

user_signed_up = Signal(providing_args=['request', 'user'])
invitation_created = Signal(providing_args=['request', 'invitation'])
invitation_used = Signal(providing_args=['request', 'invitation', 'user'])
password_changed = Signal(providing_args=['user', 'password'])

@receiver(post_save)
# pylint: disable=unused-argument
def invalidate_policy_cache(sender, instance, **_):
    """Invalidate Policy cache when policy is updated"""
    from passbook.core.models import Policy
    if isinstance(instance, Policy):
        LOGGER.debug("Invalidating policy cache", policy=instance)
        keys = cache.keys("%s#*" % instance.pk)
        cache.delete_many(keys)
        LOGGER.debug("Deleted %d keys", len(keys))
