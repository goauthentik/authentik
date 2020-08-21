"""Flow models"""
from typing import TYPE_CHECKING, Optional, Type
from uuid import uuid4

from django.db import models
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager
from rest_framework.serializers import BaseSerializer
from structlog import get_logger

from passbook.core.types import UIUserSettings
from passbook.lib.models import SerializerModel
from passbook.policies.models import PolicyBindingModel

if TYPE_CHECKING:
    from passbook.flows.stage import StageView

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
    STAGE_SETUP = "stage_setup"


class Stage(SerializerModel):
    """Stage is an instance of a component used in a flow. This can verify the user,
    enroll the user or offer a way of recovery"""

    stage_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField()

    objects = InheritanceManager()

    def type(self) -> Type["StageView"]:
        """Return StageView class that implements logic for this stage"""
        # This is a bit of a workaround, since we can't set class methods with setattr
        if hasattr(self, "__in_memory_type"):
            return getattr(self, "__in_memory_type")
        raise NotImplementedError

    def form(self) -> Type[ModelForm]:
        """Return Form class used to edit this object"""
        raise NotImplementedError

    @property
    def ui_user_settings(self) -> Optional[UIUserSettings]:
        """Entrypoint to integrate with User settings. Can either return None if no
        user settings are available, or an instanace of UIUserSettings."""
        return None

    def __str__(self):
        if hasattr(self, "__in_memory_type"):
            return f"In-memory Stage {getattr(self, '__in_memory_type')}"
        return f"Stage {self.name}"


def in_memory_stage(view: Type["StageView"]) -> Stage:
    """Creates an in-memory stage instance, based on a `_type` as view."""
    stage = Stage()
    # Because we can't pickle a locally generated function,
    # we set the view as a separate property and reference a generic function
    # that returns that member
    setattr(stage, "__in_memory_type", view)
    return stage


class Flow(SerializerModel, PolicyBindingModel):
    """Flow describes how a series of Stages should be executed to authenticate/enroll/recover
    a user. Additionally, policies can be applied, to specify which users
    have access to this flow."""

    flow_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField()
    slug = models.SlugField(unique=True)

    designation = models.CharField(max_length=100, choices=FlowDesignation.choices)

    stages = models.ManyToManyField(Stage, through="FlowStageBinding", blank=True)

    @property
    def serializer(self) -> BaseSerializer:
        from passbook.flows.api import FlowSerializer

        return FlowSerializer

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


class FlowStageBinding(SerializerModel, PolicyBindingModel):
    """Relationship between Flow and Stage. Order is required and unique for
    each flow-stage Binding. Additionally, policies can be specified, which determine if
    this Binding applies to the current user"""

    fsb_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    target = models.ForeignKey("Flow", on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)

    re_evaluate_policies = models.BooleanField(
        default=False,
        help_text=_(
            "When this option is enabled, the planner will re-evaluate policies bound to this."
        ),
    )

    order = models.IntegerField()

    objects = InheritanceManager()

    @property
    def serializer(self) -> BaseSerializer:
        from passbook.flows.api import FlowStageBindingSerializer

        return FlowStageBindingSerializer

    def __str__(self) -> str:
        return f"Flow Binding {self.target} -> {self.stage}"

    class Meta:

        ordering = ["order", "target"]

        verbose_name = _("Flow Stage Binding")
        verbose_name_plural = _("Flow Stage Bindings")
        unique_together = (("target", "stage", "order"),)
