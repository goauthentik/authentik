"""passbook expression Policy Models"""
from django.db import models
from django.utils.translation import gettext as _

from passbook.core.models import Policy
from passbook.policies.expression.evaluator import Evaluator
from passbook.policies.types import PolicyRequest, PolicyResult


class ExpressionPolicy(Policy):
    """Jinja2-based Expression policy that allows Admins to write their own logic"""

    expression = models.TextField()

    form = "passbook.policies.expression.forms.ExpressionPolicyForm"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Evaluate and render expression. Returns PolicyResult(false) on error."""
        return Evaluator().evaluate(self.expression, request)

    def save(self, *args, **kwargs):
        Evaluator().validate(self.expression)
        return super().save(*args, **kwargs)

    class Meta:

        verbose_name = _("Expression Policy")
        verbose_name_plural = _("Expression Policies")
