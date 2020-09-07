"""Policy base models"""
from typing import Type
from uuid import uuid4

from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager
from rest_framework.serializers import BaseSerializer

from passbook.lib.models import (
    CreatedUpdatedModel,
    InheritanceAutoManager,
    InheritanceForeignKey,
    SerializerModel,
)
from passbook.policies.exceptions import PolicyException
from passbook.policies.types import PolicyRequest, PolicyResult


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

    policy = InheritanceForeignKey("Policy", on_delete=models.CASCADE, related_name="+")
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

    @property
    def serializer(self) -> BaseSerializer:
        from passbook.policies.api import PolicyBindingSerializer

        return PolicyBindingSerializer

    def __str__(self) -> str:
        return f"PolicyBinding policy={self.policy} target={self.target} order={self.order}"

    class Meta:

        verbose_name = _("Policy Binding")
        verbose_name_plural = _("Policy Bindings")
        unique_together = ("policy", "target", "order")


class Policy(SerializerModel, CreatedUpdatedModel):
    """Policies which specify if a user is authorized to use an Application. Can be overridden by
    other types to add other fields, more logic, etc."""

    policy_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField(blank=True, null=True)

    objects = InheritanceAutoManager()

    def form(self) -> Type[ModelForm]:
        """Return Form class used to edit this object"""
        raise NotImplementedError

    def __str__(self):
        return f"Policy {self.name}"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Check if user instance passes this policy"""
        raise PolicyException()

    class Meta:
        base_manager_name = "objects"

        verbose_name = _("Policy")
        verbose_name_plural = _("Policies")
