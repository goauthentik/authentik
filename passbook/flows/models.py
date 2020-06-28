"""Flow models"""
from typing import Callable, Optional
from uuid import uuid4

from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager
from structlog import get_logger
from django.template.context import RequestContext

from passbook.core.types import UIUserSettings
from passbook.lib.utils.reflection import class_to_path
from passbook.policies.models import PolicyBindingModel

LOGGER = get_logger()


class NotConfiguredAction(models.TextChoices):
    """Decides how the FlowExecutor should proceed when a stage isn't configured"""

    SKIP = "skip"
    # CONFIGURE = "configure"


class FlowDesignation(models.TextChoices):
    """Designation of what a Flow should be used for. At a later point, this
    should be replaced by a database entry."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INVALIDATION = "invalidation"
    ENROLLMENT = "enrollment"
    UNRENOLLMENT = "unenrollment"
    RECOVERY = "recovery"
    USER_SETTINGS = "user_settings"


class Stage(models.Model):
    """Stage is an instance of a component used in a flow. This can verify the user,
    enroll the user or offer a way of recovery"""

    stage_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField()

    objects = InheritanceManager()
    type = ""
    form = ""

    @staticmethod
    def ui_user_settings(context: RequestContext) -> Optional[UIUserSettings]:
        """Entrypoint to integrate with User settings. Can either return None if no
        user settings are available, or an instanace of UIUserSettings."""
        return None

    def __str__(self):
        return f"Stage {self.name}"


def in_memory_stage(_type: Callable) -> Stage:
    """Creates an in-memory stage instance, based on a `_type` as view."""
    class_path = class_to_path(_type)
    stage = Stage()
    stage.type = class_path
    return stage


class Flow(PolicyBindingModel):
    """Flow describes how a series of Stages should be executed to authenticate/enroll/recover
    a user. Additionally, policies can be applied, to specify which users
    have access to this flow."""

    flow_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField()
    slug = models.SlugField(unique=True)

    designation = models.CharField(max_length=100, choices=FlowDesignation.choices)

    stages = models.ManyToManyField(Stage, through="FlowStageBinding", blank=True)

    pbm = models.OneToOneField(
        PolicyBindingModel, parent_link=True, on_delete=models.CASCADE, related_name="+"
    )

    @staticmethod
    def with_policy(request: HttpRequest, **flow_filter) -> Optional["Flow"]:
        """Get a Flow by `**flow_filter` and check if the request from `request` can access it."""
        from passbook.policies.engine import PolicyEngine

        flows = Flow.objects.filter(**flow_filter)
        for flow in flows:
            engine = PolicyEngine(flow, request.user, request)
            engine.build()
            result = engine.result
            if result.passing:
                LOGGER.debug("with_policy: flow passing", flow=flow)
                return flow
            LOGGER.warning(
                "with_policy: flow not passing", flow=flow, messages=result.messages
            )
        LOGGER.debug("with_policy: no flow found", filters=flow_filter)
        return None

    def related_flow(self, designation: str, request: HttpRequest) -> Optional["Flow"]:
        """Get a related flow with `designation`. Currently this only queries
        Flows by `designation`, but will eventually use `self` for related lookups."""
        return Flow.with_policy(request, designation=designation)

    def __str__(self) -> str:
        return f"Flow {self.name} ({self.slug})"

    class Meta:

        verbose_name = _("Flow")
        verbose_name_plural = _("Flows")


class FlowStageBinding(PolicyBindingModel):
    """Relationship between Flow and Stage. Order is required and unique for
    each flow-stage Binding. Additionally, policies can be specified, which determine if
    this Binding applies to the current user"""

    fsb_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    flow = models.ForeignKey("Flow", on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)

    re_evaluate_policies = models.BooleanField(
        default=False,
        help_text=_(
            "When this option is enabled, the planner will re-evaluate policies bound to this."
        ),
    )

    order = models.IntegerField()

    objects = InheritanceManager()

    def __str__(self) -> str:
        return f"Flow Stage Binding #{self.order} {self.flow} -> {self.stage}"

    class Meta:

        ordering = ["order", "flow"]

        verbose_name = _("Flow Stage Binding")
        verbose_name_plural = _("Flow Stage Bindings")
        unique_together = (("flow", "stage", "order"),)
