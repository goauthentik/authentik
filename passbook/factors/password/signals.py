"""passbook password factor signals"""
from django.dispatch import receiver

from passbook.core.signals import password_changed
from passbook.factors.password.exceptions import PasswordPolicyInvalid


@receiver(password_changed)
def password_policy_checker(sender, password, **_):
    """Run password through all password policies which are applied to the user"""
    from passbook.factors.password.models import PasswordFactor
    from passbook.policies.engine import PolicyEngine
    setattr(sender, '__password__', password)
    _all_factors = PasswordFactor.objects.filter(enabled=True).order_by('order')
    for factor in _all_factors:
        policy_engine = PolicyEngine(factor.password_policies.all().select_subclasses(), sender)
        policy_engine.build()
        passing, messages = policy_engine.result
        if not passing:
            raise PasswordPolicyInvalid(*messages)
