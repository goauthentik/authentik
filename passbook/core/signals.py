"""passbook core signals"""
from logging import getLogger

from django.core.cache import cache
from django.core.signals import Signal
from django.db.models.signals import post_save
from django.dispatch import receiver

from passbook.core.exceptions import PasswordPolicyInvalid

LOGGER = getLogger(__name__)

user_signed_up = Signal(providing_args=['request', 'user'])
invitation_created = Signal(providing_args=['request', 'invitation'])
invitation_used = Signal(providing_args=['request', 'invitation', 'user'])
password_changed = Signal(providing_args=['user', 'password'])

@receiver(password_changed)
# pylint: disable=unused-argument
def password_policy_checker(sender, password, **kwargs):
    """Run password through all password policies which are applied to the user"""
    from passbook.core.models import PasswordFactor
    from passbook.policy.engine import PolicyEngine
    setattr(sender, '__password__', password)
    _all_factors = PasswordFactor.objects.filter(enabled=True).order_by('order')
    for factor in _all_factors:
        policy_engine = PolicyEngine(factor.password_policies.all().select_subclasses())
        policy_engine.for_user(sender).build()
        passing, messages = policy_engine.result
        if not passing:
            raise PasswordPolicyInvalid(*messages)

@receiver(post_save)
# pylint: disable=unused-argument
def invalidate_policy_cache(sender, instance, **kwargs):
    """Invalidate Policy cache when policy is updated"""
    from passbook.core.models import Policy
    if isinstance(instance, Policy):
        LOGGER.debug("Invalidating cache for %s", instance.pk)
        keys = cache.keys("%s#*" % instance.pk)
        cache.delete_many(keys)
        LOGGER.debug("Deleted %d keys", len(keys))
