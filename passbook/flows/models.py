"""Flow models"""
from enum import Enum
from typing import Tuple

from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Factor
from passbook.lib.models import UUIDModel
from passbook.policies.models import PolicyBindingModel


class FlowDesignation(Enum):
    """Designation of what a Flow should be used for. At a later point, this
    should be replaced by a database entry."""

    AUTHENTICATION = "authentication"
    ENROLLMENT = "enrollment"
    RECOVERY = "recovery"

    @staticmethod
    def as_choices() -> Tuple[Tuple[str, str]]:
        """Generate choices of actions used for database"""
        return tuple(
            (x, y.value) for x, y in getattr(FlowDesignation, "__members__").items()
        )


class Flow(PolicyBindingModel, UUIDModel):
    """Flow describes how a series of Factors should be executed to authenticate/enroll/recover
    a user. Additionally, policies can be applied, to specify which users
    have access to this flow."""

    name = models.TextField()
    slug = models.SlugField(unique=True)

    designation = models.CharField(max_length=100, choices=FlowDesignation.as_choices())

    factors = models.ManyToManyField(Factor, through="FlowFactorBinding", blank=True)

    pbm = models.OneToOneField(
        PolicyBindingModel, parent_link=True, on_delete=models.CASCADE, related_name="+"
    )

    def __str__(self) -> str:
        return f"Flow {self.name} ({self.slug})"

    class Meta:

        verbose_name = _("Flow")
        verbose_name_plural = _("Flows")


class FlowFactorBinding(PolicyBindingModel, UUIDModel):
    """Relationship between Flow and Factor. Order is required and unique for
    each flow-factor Binding. Additionally, policies can be specified, which determine if
    this Binding applies to the current user"""

    flow = models.ForeignKey("Flow", on_delete=models.CASCADE)
    factor = models.ForeignKey(Factor, on_delete=models.CASCADE)

    re_evaluate_policies = models.BooleanField(
        default=False,
        help_text=_(
            "When this option is enabled, the planner will re-evaluate policies bound to this."
        ),
    )

    order = models.IntegerField()

    def __str__(self) -> str:
        return f"Flow Factor Binding #{self.order} {self.flow} -> {self.factor}"

    class Meta:

        ordering = ["order", "flow"]

        verbose_name = _("Flow Factor Binding")
        verbose_name_plural = _("Flow Factor Bindings")
        unique_together = (("flow", "factor", "order"),)
