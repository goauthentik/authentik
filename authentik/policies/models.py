"""Policy base models"""
from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager
from rest_framework.serializers import BaseSerializer

from authentik.lib.models import (
    CreatedUpdatedModel,
    InheritanceAutoManager,
    InheritanceForeignKey,
    SerializerModel,
)
from authentik.policies.exceptions import PolicyException
from authentik.policies.types import PolicyRequest, PolicyResult


class PolicyEngineMode(models.TextChoices):
    """Decide how results of multiple policies should be combined."""

    MODE_ALL = "all", _("all, all policies must pass")  # type: "PolicyEngineMode"
    MODE_ANY = "any", _("any, any policy must pass")  # type: "PolicyEngineMode"


class PolicyBindingModel(models.Model):
    """Base Model for objects that have policies applied to them."""

    pbm_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    policies = models.ManyToManyField(
        "Policy", through="PolicyBinding", related_name="bindings", blank=True
    )

    policy_engine_mode = models.TextField(
        choices=PolicyEngineMode.choices,
        default=PolicyEngineMode.MODE_ANY,
    )

    objects = InheritanceManager()

    def __str__(self) -> str:
        return f"PolicyBindingModel {self.pbm_uuid}"

    class Meta:
        verbose_name = _("Policy Binding Model")
        verbose_name_plural = _("Policy Binding Models")


class PolicyBinding(SerializerModel):
    """Relationship between a Policy and a PolicyBindingModel."""

    policy_binding_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    enabled = models.BooleanField(default=True)

    policy = InheritanceForeignKey(
        "Policy",
        on_delete=models.CASCADE,
        related_name="+",
        default=None,
        null=True,
        blank=True,
    )
    group = models.ForeignKey(
        # This is quite an ugly hack to prevent pylint from trying
        # to resolve authentik_core.models.Group
        # as python import path
        "authentik_core.Group",
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        "authentik_core.User",
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
    )

    target = InheritanceForeignKey(PolicyBindingModel, on_delete=models.CASCADE, related_name="+")
    negate = models.BooleanField(
        default=False,
        help_text=_("Negates the outcome of the policy. Messages are unaffected."),
    )
    timeout = models.PositiveIntegerField(
        default=30, help_text=_("Timeout after which Policy execution is terminated.")
    )
    failure_result = models.BooleanField(
        default=False, help_text=_("Result if the Policy execution fails.")
    )

    order = models.IntegerField()

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Check if request passes this PolicyBinding, check policy, group or user"""
        if self.policy:
            self.policy: Policy
            return self.policy.passes(request)
        if self.group:
            return PolicyResult(self.group.is_member(request.user))
        if self.user:
            return PolicyResult(request.user == self.user)
        return PolicyResult(False)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.api.bindings import PolicyBindingSerializer

        return PolicyBindingSerializer

    @property
    def target_type(self) -> str:
        """Get the target type this binding is applied to"""
        if self.policy:
            return "policy"
        if self.group:
            return "group"
        if self.user:
            return "user"
        return "invalid"

    @property
    def target_name(self) -> str:
        """Get the target name this binding is applied to"""
        if self.policy:
            return self.policy.name
        if self.group:
            return self.group.name
        if self.user:
            return self.user.name
        return "invalid"

    def __str__(self) -> str:
        suffix = f"{self.target_type.title()} {self.target_name}"
        try:
            return f"Binding from {self.target} #{self.order} to {suffix}"
        except PolicyBinding.target.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            return f"Binding - #{self.order} to {suffix}"
        return ""

    class Meta:
        verbose_name = _("Policy Binding")
        verbose_name_plural = _("Policy Bindings")
        unique_together = ("policy", "target", "order")
        indexes = [
            models.Index(fields=["policy"]),
            models.Index(fields=["group"]),
            models.Index(fields=["user"]),
            models.Index(fields=["target"]),
        ]


class Policy(SerializerModel, CreatedUpdatedModel):
    """Policies which specify if a user is authorized to use an Application. Can be overridden by
    other types to add other fields, more logic, etc."""

    policy_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField(unique=True)

    execution_logging = models.BooleanField(
        default=False,
        help_text=_(
            "When this option is enabled, all executions of this policy will be logged. "
            "By default, only execution errors are logged."
        ),
    )

    objects = InheritanceAutoManager()

    @property
    def component(self) -> str:
        """Return component used to edit this object"""
        raise NotImplementedError

    def __str__(self):
        return str(self.name)

    def passes(self, request: PolicyRequest) -> PolicyResult:  # pragma: no cover
        """Check if request passes this policy"""
        raise PolicyException()

    class Meta:
        base_manager_name = "objects"

        verbose_name = _("Policy")
        verbose_name_plural = _("Policies")

        permissions = [
            ("view_policy_cache", _("View Policy's cache metrics")),
            ("clear_policy_cache", _("Clear Policy's cache metrics")),
        ]

    class PolicyMeta:
        """Base class for the Meta class for all policies"""

        indexes = [
            models.Index(fields=["policy_ptr_id"]),
        ]
