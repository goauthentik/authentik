"""Flow models"""
from typing import Optional

from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager

from passbook.core.types import UIUserSettings
from passbook.lib.models import UUIDModel
from passbook.policies.models import PolicyBindingModel


class FlowDesignation(models.TextChoices):
    """Designation of what a Flow should be used for. At a later point, this
    should be replaced by a database entry."""

    AUTHENTICATION = "authentication"
    ENROLLMENT = "enrollment"
    RECOVERY = "recovery"
    PASSWORD_CHANGE = "password_change"  # nosec # noqa


class Stage(UUIDModel):
    """Stage is an instance of a component used in a flow. This can verify the user,
    enroll the user or offer a way of recovery"""

    name = models.TextField()

    objects = InheritanceManager()
    type = ""
    form = ""

    @property
    def ui_user_settings(self) -> Optional[UIUserSettings]:
        """Entrypoint to integrate with User settings. Can either return None if no
        user settings are available, or an instanace of UIUserSettings."""
        return None

    def __str__(self):
        return f"Stage {self.name}"


class Flow(PolicyBindingModel, UUIDModel):
    """Flow describes how a series of Stages should be executed to authenticate/enroll/recover
    a user. Additionally, policies can be applied, to specify which users
    have access to this flow."""

    name = models.TextField()
    slug = models.SlugField(unique=True)

    designation = models.CharField(max_length=100, choices=FlowDesignation.choices)

    stages = models.ManyToManyField(Stage, through="FlowStageBinding", blank=True)

    pbm = models.OneToOneField(
        PolicyBindingModel, parent_link=True, on_delete=models.CASCADE, related_name="+"
    )

    def related_flow(self, designation: str) -> Optional["Flow"]:
        """Get a related flow with `designation`. Currently this only queries
        Flows by `designation`, but will eventually use `self` for related lookups."""
        return Flow.objects.filter(designation=designation).first()

    def __str__(self) -> str:
        return f"Flow {self.name} ({self.slug})"

    class Meta:

        verbose_name = _("Flow")
        verbose_name_plural = _("Flows")


class FlowStageBinding(PolicyBindingModel, UUIDModel):
    """Relationship between Flow and Stage. Order is required and unique for
    each flow-stage Binding. Additionally, policies can be specified, which determine if
    this Binding applies to the current user"""

    flow = models.ForeignKey("Flow", on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)

    re_evaluate_policies = models.BooleanField(
        default=False,
        help_text=_(
            "When this option is enabled, the planner will re-evaluate policies bound to this."
        ),
    )

    order = models.IntegerField()

    def __str__(self) -> str:
        return f"Flow Stage Binding #{self.order} {self.flow} -> {self.stage}"

    class Meta:

        ordering = ["order", "flow"]

        verbose_name = _("Flow Stage Binding")
        verbose_name_plural = _("Flow Stage Bindings")
        unique_together = (("flow", "stage", "order"),)
