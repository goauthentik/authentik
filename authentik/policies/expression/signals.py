from django.db.models.signals import pre_save
from django.dispatch import receiver

from authentik.policies.expression.evaluator import PolicyEvaluator
from authentik.policies.expression.models import ExpressionPolicy


@receiver(pre_save, sender=ExpressionPolicy)
def pre_save_expression_policy(sender: type[ExpressionPolicy], instance: ExpressionPolicy, **_):
    """Ensure policy is valid before saving"""
    evaluator = PolicyEvaluator(instance.execution_user, instance.name)
    evaluator.policy = instance
    evaluator.validate(instance.expression)
