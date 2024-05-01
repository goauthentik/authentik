"""authentik expression Policy Models"""

from django.db import models
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer

from authentik.policies.expression.evaluator import PolicyEvaluator
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult


class ExpressionPolicy(Policy):
    """Execute arbitrary Python code to implement custom checks and validation."""

    execution_user = models.ForeignKey(
        "authentik_core.User", default=None, null=True, on_delete=models.SET_DEFAULT
    )
    expression = models.TextField()

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.expression.api import ExpressionPolicySerializer

        return ExpressionPolicySerializer

    @property
    def component(self) -> str:
        return "ak-policy-expression-form"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Evaluate and render expression. Returns PolicyResult(false) on error."""
        evaluator = PolicyEvaluator(self.execution_user, self.name)
        evaluator.policy = self
        evaluator.set_policy_request(request)
        return evaluator.evaluate(self.expression)

    class Meta(Policy.PolicyMeta):
        verbose_name = _("Expression Policy")
        verbose_name_plural = _("Expression Policies")
