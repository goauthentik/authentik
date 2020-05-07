"""Policy base models"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Policy
from passbook.lib.models import UUIDModel


class PolicyBindingModel(models.Model):
    """Base Model for objects which have Policies applied to them"""

    policies = models.ManyToManyField(Policy, through="PolicyBinding", related_name="+")


class PolicyBinding(UUIDModel):
    """Relationship between a Policy and a PolicyBindingModel."""

    enabled = models.BooleanField(default=True)

    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name="+")
    target = models.ForeignKey(
        PolicyBindingModel, on_delete=models.CASCADE, related_name="+"
    )

    # default value and non-unique for compatibility
    order = models.IntegerField(default=0)

    class Meta:

        verbose_name = _("Policy Binding")
        verbose_name_plural = _("Policy Bindings")
