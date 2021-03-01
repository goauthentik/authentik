"""Policy base models"""
from typing import Type
from uuid import uuid4

from django.db import models
from django.forms import ModelForm
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


class PolicyBindingModel(models.Model):
    """Base Model for objects that have policies applied to them."""

    pbm_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    policies = models.ManyToManyField(
        "Policy", through="PolicyBinding", related_name="bindings", blank=True
    )

    objects = InheritanceManager()

    class Meta:
        verbose_name = _("Policy Binding Model")
        verbose_name_plural = _("Policy Binding Models")


class PolicyBinding(SerializerModel):
    """Relationship between a Policy and a PolicyBindingModel."""

    policy_binding_uuid = models.UUIDField(
        primary_key=True, editable=False, default=uuid4
    )

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
        "authentik_core." + "Group",
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        "authentik_core." + "User",
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
    )

    target = InheritanceForeignKey(
        PolicyBindingModel, on_delete=models.CASCADE, related_name="+"
    )
    negate = models.BooleanField(
        default=False,
        help_text=_("Negates the outcome of the policy. Messages are unaffected."),
    )
    timeout = models.IntegerField(
        default=30, help_text=_("Timeout after which Policy execution is terminated.")
    )

    order = models.IntegerField()

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Check if request passes this PolicyBinding, check policy, group or user"""
        if self.policy:
            self.policy: Policy
            return self.policy.passes(request)
        if self.group:
            return PolicyResult(self.group.users.filter(pk=request.user.pk).exists())
        if self.user:
            return PolicyResult(request.user == self.user)
        return PolicyResult(False)

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.policies.api import PolicyBindingSerializer

        return PolicyBindingSerializer

    def __str__(self) -> str:
        try:
            return f"Policy Binding {self.target} #{self.order} {self.policy}"
        except PolicyBinding.target.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            return f"Policy Binding - #{self.order} {self.policy}"

    class Meta:

        verbose_name = _("Policy Binding")
        verbose_name_plural = _("Policy Bindings")
        unique_together = ("policy", "target", "order")


class Policy(SerializerModel, CreatedUpdatedModel):
    """Policies which specify if a user is authorized to use an Application. Can be overridden by
    other types to add other fields, more logic, etc."""

    policy_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField(blank=True, null=True)

    execution_logging = models.BooleanField(
        default=False,
        help_text=_(
            (
                "When this option is enabled, all executions of this policy will be logged. "
                "By default, only execution errors are logged."
            )
        ),
    )

    objects = InheritanceAutoManager()

    @property
    def form(self) -> Type[ModelForm]:
        """Return Form class used to edit this object"""
        raise NotImplementedError

    def __str__(self):
        return self.name

    def passes(self, request: PolicyRequest) -> PolicyResult:  # pragma: no cover
        """Check if request passes this policy"""
        raise PolicyException()

    class Meta:
        base_manager_name = "objects"

        verbose_name = _("Policy")
        verbose_name_plural = _("Policies")
