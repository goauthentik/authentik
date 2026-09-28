"""authentik conditional policy models"""

from django.db import models
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import BaseSerializer

from authentik.policies.conditional.evaluator import (
    CompiledAction,
    CompiledPolicyRef,
    ConditionEvaluator,
    ConditionValidationError,
    compile_actions,
    iter_conditions,
    iter_requirements,
)
from authentik.policies.conditional.registry import Setter, Variable, registry
from authentik.policies.conditional.schema import SCHEMA_VERSION
from authentik.policies.exceptions import PolicyException
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult


def default_actions() -> dict:
    return {"version": SCHEMA_VERSION, "actions": []}


class MissingBehavior(models.TextChoices):
    """What to do when a variable's value is not available"""

    FAIL = "fail", _("Fail the policy")
    FALSE = "false", _("Evaluate the condition as false")


class ConditionalPolicy(Policy):
    """Run actions and check conditions on values provided by authentik, without writing
    code."""

    actions = models.JSONField(default=default_actions)
    missing_behavior = models.TextField(
        choices=MissingBehavior.choices,
        default=MissingBehavior.FAIL,
        help_text=_("How to handle values which are not available in the request."),
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

    def compiled(self) -> tuple[CompiledAction, ...]:
        """Compiled actions, cached on the instance"""
        cached = getattr(self, "_compiled", None)
        if cached and cached[0] is self.actions:
            return cached[1]
        compiled = compile_actions(self.actions)
        self._compiled = (self.actions, compiled)
        return compiled

    def passes(self, request: PolicyRequest) -> PolicyResult:
        try:
            actions = self.compiled()
        except ConditionValidationError as exc:
            raise PolicyException(exc) from exc
        return ConditionEvaluator(request, self.missing_behavior, self.failure_message or None).run(
            actions
        )

    def used_requirements(self, _seen: set[str] | None = None) -> set[Variable | Setter]:
        """All variables and setters used by this policy, including referenced conditional
        policies"""
        seen = _seen if _seen is not None else set()
        seen.add(str(self.pk))
        actions = self.compiled()
        used: set[Variable | Setter] = set(iter_requirements(actions))
        for node in iter_conditions(actions):
            if not isinstance(node, CompiledPolicyRef) or node.policy in seen:
                continue
            referenced = ConditionalPolicy.objects.filter(pk=node.policy).first()
            if referenced:
                used |= referenced.used_requirements(seen)
        return used

    def validate_target(self, target: models.Model):
        try:
            used = self.used_requirements()
        except ConditionValidationError:
            return
        facts = registry.facts_for_target(target._meta.label_lower)
        unavailable = sorted({item.key for item in used if not item.available_for(facts)})
        if unavailable:
            raise ValidationError(
                _(
                    "Policy '{policy}' uses values which are not available for "
                    "{target}: {values}"
                ).format(
                    policy=self.name,
                    target=target._meta.verbose_name,
                    values=", ".join(unavailable),
                )
            )

    class Meta(Policy.PolicyMeta):
        verbose_name = _("Conditional Policy")
        verbose_name_plural = _("Conditional Policies")
