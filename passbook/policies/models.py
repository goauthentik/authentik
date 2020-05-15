"""Policy base models"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager

from passbook.lib.models import CreatedUpdatedModel, UUIDModel
from passbook.policies.exceptions import PolicyException
from passbook.policies.types import PolicyRequest, PolicyResult


class Policy(UUIDModel, CreatedUpdatedModel):
    """Policies which specify if a user is authorized to use an Application. Can be overridden by
    other types to add other fields, more logic, etc."""

    name = models.TextField(blank=True, null=True)
    negate = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    timeout = models.IntegerField(default=30)

    objects = InheritanceManager()

    def __str__(self):
        return f"Policy {self.name}"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Check if user instance passes this policy"""
        raise PolicyException()


class PolicyBindingModel(models.Model):
    """Base Model for objects that have policies applied to them."""

    policies = models.ManyToManyField(
        Policy, through="PolicyBinding", related_name="+", blank=True
    )

    class Meta:

        verbose_name = _("Policy Binding Model")
        verbose_name_plural = _("Policy Binding Models")


class PolicyBinding(UUIDModel):
    """Relationship between a Policy and a PolicyBindingModel."""

    enabled = models.BooleanField(default=True)

    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name="+")
    target = models.ForeignKey(
        PolicyBindingModel, on_delete=models.CASCADE, related_name="+"
    )

    # default value and non-unique for compatibility
    order = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"PolicyBinding policy={self.policy} target={self.target} order={self.order}"

    class Meta:

        verbose_name = _("Policy Binding")
        verbose_name_plural = _("Policy Bindings")
