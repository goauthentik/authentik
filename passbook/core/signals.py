"""passbook core signals"""

from django.core.signals import Signal
from django.dispatch import receiver

from passbook.core.exceptions import PasswordPolicyInvalid

user_signed_up = Signal(providing_args=['request', 'user'])
invitation_created = Signal(providing_args=['request', 'invitation'])
invitation_used = Signal(providing_args=['request', 'invitation', 'user'])
password_changed = Signal(providing_args=['user', 'password'])

@receiver(password_changed)
# pylint: disable=unused-argument
def password_policy_checker(sender, password, **kwargs):
    """Run password through all password policies which are applied to the user"""
    from passbook.core.models import PasswordFactor
    from passbook.core.policies import PolicyEngine
    setattr(sender, '__password__', password)
    _all_factors = PasswordFactor.objects.filter(enabled=True).order_by('order')
    for factor in _all_factors:
        if factor.passes(sender):
            policy_engine = PolicyEngine(factor.password_policies.all().select_subclasses())
            policy_engine.for_user(sender)
            passing, messages = policy_engine.result
            if not passing:
                raise PasswordPolicyInvalid(*messages)
