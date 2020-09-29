"""passbook expression Policy Models"""
from typing import Type

from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer

from passbook.policies.expression.evaluator import PolicyEvaluator
from passbook.policies.models import Policy
from passbook.policies.types import PolicyRequest, PolicyResult


class ExpressionPolicy(Policy):
    """Execute arbitrary Python code to implement custom checks and validation."""

    expression = models.TextField()

    @property
    def serializer(self) -> BaseSerializer:
        from passbook.policies.expression.api import ExpressionPolicySerializer

        return ExpressionPolicySerializer

    @property
    def form(self) -> Type[ModelForm]:
        from passbook.policies.expression.forms import ExpressionPolicyForm

        return ExpressionPolicyForm

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
