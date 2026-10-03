"""authentik conditional policy models"""

from typing import Any

from django.db import models
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import BaseSerializer

from authentik.policies.conditional.evaluator import (
    CompiledPolicy,
    ConditionCompiler,
    ConditionEvaluator,
)
from authentik.policies.conditional.registry import registry
from authentik.policies.conditional.schema import (
    SCHEMA_VERSION,
    ConditionValidationError,
    MissingBehavior,
)
from authentik.policies.exceptions import PolicyException
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult


def default_actions() -> dict:
    return {"version": SCHEMA_VERSION, "actions": []}


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

    def __getstate__(self) -> dict[str, Any]:
        # Policies are pickled with their results, for example to cache them. Compiled actions
        # contain functions of variables which can't be pickled, and are compiled again.
        state = super().__getstate__()
        state.pop("_compiled", None)
        return state

    def compiled(self) -> CompiledPolicy:
        """Compiled actions, cached on the instance"""
        cached = getattr(self, "_compiled", None)
        if not cached or cached[0] is not self.actions:
            cached = self._compiled = (self.actions, ConditionCompiler.compile(self.actions))
        return cached[1]

    def passes(self, request: PolicyRequest) -> PolicyResult:
        try:
            actions = self.compiled().actions
        except ConditionValidationError as exc:
            raise PolicyException(exc) from exc
        return ConditionEvaluator(request, self.missing_behavior, self.failure_message).run(actions)

    def validate_target(self, target: models.Model):
        """Check that all variables and setters used by this policy, and by referenced
        conditional policies, are available where the policy is bound"""
        facts = registry.facts_for_target(target._meta.label_lower)
        unavailable, seen, pending = set(), set(), [self]
        while pending:
            policy = pending.pop()
            seen.add(str(policy.pk))
            try:
                compiled = policy.compiled()
            except ConditionValidationError:
                continue
            unavailable |= {
                item.key for item in compiled.requirements if item.requires.isdisjoint(facts)
            }
            references = [ref.policy for ref in compiled.references if ref.policy not in seen]
            pending.extend(ConditionalPolicy.objects.filter(pk__in=references))
        if unavailable:
            raise ValidationError(
                _(
                    "Policy '{policy}' uses values which are not available for "
                    "{target}: {values}"
                ).format(
                    policy=self.name,
                    target=target._meta.verbose_name,
                    values=", ".join(sorted(unavailable)),
                )
            )

    class Meta(Policy.PolicyMeta):
        verbose_name = _("Conditional Policy")
        verbose_name_plural = _("Conditional Policies")
