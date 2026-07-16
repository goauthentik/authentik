from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _

from authentik.lib.models import CreatedUpdatedModel, SerializerModel
from authentik.policies.models import PolicyBindingModel


class RequestRuleChildBinding(SerializerModel):
    """Binding between request rule binding and a child/related model"""

    uuid = models.UUIDField(default=uuid4, primary_key=True)
    binding = models.ForeignKey("RequestRuleBinding", on_delete=models.CASCADE)
    target = models.ForeignKey(PolicyBindingModel, on_delete=models.CASCADE, related_name="+")

    class Meta:
        verbose_name = _("Request Rule Child Binding")
        verbose_name_plural = _("Request Rule Child Bindings")
        unique_together = ("binding", "target")


class RequestRuleBinding(SerializerModel, PolicyBindingModel):
    """Binding between a request rule and a requestable model, optionally also
    carrying n RequestableChildModel"""

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    rule = models.ForeignKey("RequestRule", on_delete=models.CASCADE)
    target = models.ForeignKey(
        PolicyBindingModel, on_delete=models.CASCADE, related_name="request_rule_bindings"
    )
    related = models.ManyToManyField(
        PolicyBindingModel,
        through=RequestRuleChildBinding,
        related_name="request_rule_child_bindings",
    )

    class Meta:
        verbose_name = _("Request Rule Binding")
        verbose_name_plural = _("Request Rule Bindings")
        unique_together = ("rule", "target")


class RequestRule(CreatedUpdatedModel, SerializerModel, PolicyBindingModel):
    """A rule defining who can request access and who can approve access to any of the
    requestable models this rule is bound to."""

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    name = models.TextField()
    targets = models.ManyToManyField(
        PolicyBindingModel,
        through=RequestRuleBinding,
        related_name="request_rules",
        through_fields=("rule", "target"),
    )

    class Meta:
        verbose_name = _("Request Rule")
        verbose_name_plural = _("Request Rules")
