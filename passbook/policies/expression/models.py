"""passbook expression Policy Models"""
from django.db import models
from django.utils.translation import gettext as _

from passbook.policies.expression.evaluator import PolicyEvaluator
from passbook.policies.models import Policy
from passbook.policies.types import PolicyRequest, PolicyResult


class ExpressionPolicy(Policy):
    """Implement custom logic using python."""

    expression = models.TextField()

    form = "passbook.policies.expression.forms.ExpressionPolicyForm"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Evaluate and render expression. Returns PolicyResult(false) on error."""
        evaluator = PolicyEvaluator(self.name)
        evaluator.set_policy_request(request)
        return evaluator.evaluate(self.expression)

    def save(self, *args, **kwargs):
        PolicyEvaluator(self.name).validate(self.expression)
        return super().save(*args, **kwargs)

    class Meta:

        verbose_name = _("Expression Policy")
        verbose_name_plural = _("Expression Policies")
