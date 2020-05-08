"""Policy base models"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Policy
from passbook.lib.models import UUIDModel


class PolicyBindingModel(models.Model):
    """Base Model for objects which have Policies applied to them"""

    policies = models.ManyToManyField(Policy, through="PolicyBinding", related_name="+")

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
