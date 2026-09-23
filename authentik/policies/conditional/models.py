"""authentik conditional policy models"""

from django.db import models
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import BaseSerializer

from authentik.policies.conditional.evaluator import (
    CompiledNode,
    CompiledPolicyRef,
    ConditionEvaluator,
    ConditionValidationError,
    compile_conditions,
    iter_nodes,
    iter_variables,
)
from authentik.policies.conditional.registry import Variable, registry
from authentik.policies.conditional.schema import SCHEMA_VERSION, GroupOp, NodeType
from authentik.policies.exceptions import PolicyException
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult


def default_conditions() -> dict:
    return {
        "version": SCHEMA_VERSION,
        "root": {"type": NodeType.GROUP, "op": GroupOp.ALL, "children": []},
    }


class MissingBehavior(models.TextChoices):
    """What to do when a variable's value is not available"""

    FAIL = "fail", _("Fail the policy")
    FALSE = "false", _("Evaluate the condition as false")


class ConditionalPolicy(Policy):
    """Evaluate conditions on variables provided by authentik, without writing code."""

    conditions = models.JSONField(default=default_conditions)
    missing_behavior = models.TextField(
        choices=MissingBehavior.choices,
        default=MissingBehavior.FAIL,
        help_text=_("How to handle conditions whose variable is not available in the request."),
    )
    failure_message = models.TextField(
        blank=True,
        default="",
        help_text=_("Message shown to the user when the policy does not pass."),
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.conditional.api import ConditionalPolicySerializer

        return ConditionalPolicySerializer

    @property
    def component(self) -> str:
        return "ak-policy-conditional-form"

    def compiled(self) -> CompiledNode:
        """Compiled condition tree, cached on the instance"""
        cached = getattr(self, "_compiled", None)
        if cached and cached[0] is self.conditions:
            return cached[1]
        compiled = compile_conditions(self.conditions)
        self._compiled = (self.conditions, compiled)
        return compiled

    def passes(self, request: PolicyRequest) -> PolicyResult:
        try:
            root = self.compiled()
        except ConditionValidationError as exc:
            raise PolicyException(exc) from exc
        result = ConditionEvaluator(request, self.missing_behavior).evaluate(root)
        if not result.passing and self.failure_message:
            result.messages = (self.failure_message,)
        return result

    def used_variables(self, _seen: set[str] | None = None) -> set[Variable]:
        """All variables used by this policy, including referenced conditional policies"""
        seen = _seen if _seen is not None else set()
        seen.add(str(self.pk))
        root = self.compiled()
        variables = set(iter_variables(root))
        for node in iter_nodes(root):
            if not isinstance(node, CompiledPolicyRef) or node.policy in seen:
                continue
            referenced = ConditionalPolicy.objects.filter(pk=node.policy).first()
            if referenced:
                variables |= referenced.used_variables(seen)
        return variables

    def validate_target(self, target: models.Model):
        try:
            used = self.used_variables()
        except ConditionValidationError:
            return
        facts = registry.facts_for_target(target._meta.label_lower)
        unavailable = sorted(variable.key for variable in used if not variable.available_for(facts))
        if unavailable:
            raise ValidationError(
                _(
                    "Policy '{policy}' uses variables which are not available for "
                    "{target}: {variables}"
                ).format(
                    policy=self.name,
                    target=target._meta.verbose_name,
                    variables=", ".join(unavailable),
                )
            )

    class Meta(Policy.PolicyMeta):
        verbose_name = _("Conditional Policy")
        verbose_name_plural = _("Conditional Policies")
