"""authentik expression Policy Models"""
from pathlib import Path

from django.db import models
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger

from authentik.blueprints.models import ManagedModel
from authentik.lib.config import CONFIG
from authentik.lib.models import CreatedUpdatedModel, SerializerModel
from authentik.policies.expression.evaluator import PolicyEvaluator
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult

LOGGER = get_logger()

MANAGED_DISCOVERED = "goauthentik.io/variables/discovered/%s"


class ExpressionVariable(SerializerModel, ManagedModel, CreatedUpdatedModel):
    """Variable that can be given to expression policies"""

    name = models.TextField(unique=True)
    value = models.TextField()

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.expression.api import ExpressionVariableSerializer

        return ExpressionVariableSerializer

    def reload(self):
        """Reload a variable from disk if it's managed"""
        if self.managed != MANAGED_DISCOVERED % self.name:
            return
        path = Path(CONFIG.get("variables_discovery_dir")) / Path(self.name)
        try:
            with open(path, "r", encoding="utf-8") as _file:
                body = _file.read()
                if body != self.value:
                    self.value = body
                    self.save()
        except (OSError, ValueError) as exc:
            LOGGER.warning(
                "Failed to reload variable, continuing anyway",
                exc=exc,
                file=path,
                variable=self.name,
            )

    class Meta:
        verbose_name = _("Expression Variable")
        verbose_name_plural = _("Expression Variables")


class ExpressionPolicy(Policy):
    """Execute arbitrary Python code to implement custom checks and validation."""

    expression = models.TextField()

    variables = models.ManyToManyField(ExpressionVariable, blank=True)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.expression.api import ExpressionPolicySerializer

        return ExpressionPolicySerializer

    @property
    def component(self) -> str:
        return "ak-policy-expression-form"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Evaluate and render expression. Returns PolicyResult(false) on error."""
        evaluator = PolicyEvaluator(self.name)
        evaluator.policy = self
        evaluator.set_policy_request(request)
        evaluator.set_variables(self.variables)
        return evaluator.evaluate(self.expression)

    def save(self, *args, **kwargs):
        evaluator = PolicyEvaluator(self.name)
        evaluator.policy = self
        evaluator.validate(self.expression)
        return super().save(*args, **kwargs)

    class Meta(Policy.PolicyMeta):
        verbose_name = _("Expression Policy")
        verbose_name_plural = _("Expression Policies")
