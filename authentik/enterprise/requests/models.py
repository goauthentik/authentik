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

    @property
    def serializer(self):
        from authentik.enterprise.requests.api.request_rule_child_bindings import (
            RequestRuleChildBindingSerializer,
        )

        return RequestRuleChildBindingSerializer

    class Meta:
        verbose_name = _("Request Rule Child Binding")
        verbose_name_plural = _("Request Rule Child Bindings")
        unique_together = ("binding", "target")


# PBM here configures who can request access
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

    @property
    def serializer(self):
        from authentik.enterprise.requests.api.request_rule_bindings import (
            RequestRuleBindingSerializer,
        )

        return RequestRuleBindingSerializer

    class Meta:
        verbose_name = _("Request Rule Binding")
        verbose_name_plural = _("Request Rule Bindings")


# PBM here configures who can approve
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

    @property
    def serializer(self):
        from authentik.enterprise.requests.api.request_rules import RequestRuleSerializer

        return RequestRuleSerializer

    class Meta:
        verbose_name = _("Request Rule")
        verbose_name_plural = _("Request Rules")
