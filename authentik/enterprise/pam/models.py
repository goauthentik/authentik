from typing import Any
from uuid import uuid4

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import CreatedUpdatedModel, ExpiringModel, User
from authentik.lib.models import InternallyManagedMixin, SerializerModel
from authentik.policies.models import PolicyBinding, PolicyBindingModel


class Persona(ExpiringModel, User):
    # Inherited:
    #  - parent.email
    #  - parent.name (customisable)
    # Modified:
    #  - parent.username
    #  - parent.groups

    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="personas")

    @staticmethod
    def create_for_user(name: str, user: User) -> Persona:
        return Persona.objects.create(username=name, name=user.name, parent=user)

    class Meta(ExpiringModel.Meta):
        verbose_name = _("Persona")
        verbose_name_plural = _("Personas")

    def __str__(self):
        return f"Persona {self.username} for {self.parent_id}"


class Grant(ExpiringModel, CreatedUpdatedModel):
    """Grant for a persona to access `target`, given after manual/automatic approval."""

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    target = models.ForeignKey(PolicyBindingModel, on_delete=models.CASCADE)

    class Meta(ExpiringModel.Meta):
        verbose_name = _("Grant")
        verbose_name_plural = _("Grants")

    def __str__(self):
        return f"Grant {self.uuid}"


class RequestStatus(models.TextChoices):

    CREATED = "created"
    APPROVED = "approved"
    DENIED = "denied"


class GrantRequest(SerializerModel, ExpiringModel, CreatedUpdatedModel):
    """Request of a user to access target(s) via Persona"""

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="grant_requests_created"
    )
    fulfilled_by = models.ForeignKey(
        User,
        on_delete=models.SET_DEFAULT,
        related_name="grant_requests_fulfilled",
        null=True,
        default=None,
    )

    # Targets access was requested to
    targets = models.ManyToManyField(PolicyBindingModel, through="GrantRequestTarget")
    # Justification data, inputted by the `created_by` user via a flow, used for approve/deny
    requester_data = models.JSONField(default=dict)
    fulfiller_data = models.JSONField(default=dict)

    status = models.TextField(choices=RequestStatus.choices, default=RequestStatus.CREATED)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.pam.api.grant_requests import GrantRequestSerializer

        return GrantRequestSerializer

    @transaction.atomic
    def fulfill(self, status: RequestStatus, user: User, data: dict[str, Any]):
        if self.status != RequestStatus.CREATED:
            return
        self.fulfilled_by = user
        self.fulfiller_data = data
        self.status = status
        self.save()
        if self.status != RequestStatus.APPROVED:
            return
        for target in GrantRequestTarget.objects.filter(request=self).all():
            target_binding = PolicyBinding.objects.create(
                user=self.created_by,
                target=target.target,
                expiring=self.expiring,
                expires=self.expires,
                order=1000,
            )
            target.binding = target_binding
            target.save()

    class Meta:
        verbose_name = _("Grant Request")
        verbose_name_plural = _("Grant Requests")

    def __str__(self):
        return f"Grant Request {self.uuid}"


class GrantRequestTarget(InternallyManagedMixin, models.Model):

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    request = models.ForeignKey(GrantRequest, on_delete=models.CASCADE)
    binding = models.ForeignKey(PolicyBinding, on_delete=models.CASCADE, null=True)
    target = models.ForeignKey(PolicyBindingModel, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Grant Request Target")
        verbose_name_plural = _("Grant Request Targets")

    def __str__(self):
        return f"Grant Request-target {self.request_id} to {self.target_id}"


class PolicyBindingModelRequestRule(SerializerModel, CreatedUpdatedModel, PolicyBindingModel):

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    name = models.TextField()
    pbm = models.ForeignKey(
        PolicyBindingModel, on_delete=models.CASCADE, related_name="request_rules"
    )

    reviewer_groups = models.ManyToManyField("authentik_core.Group", blank=True)
    min_reviewers = models.PositiveSmallIntegerField(default=1)
    min_reviewers_is_per_group = models.BooleanField(default=False)
    reviewers = models.ManyToManyField("authentik_core.User", blank=True)

    @property
    def serializer(self):
        from authentik.enterprise.pam.api.request_rules import PolicyBindingModelRequestRuleSerializer

        return PolicyBindingModelRequestRuleSerializer

    class Meta:
        verbose_name = _("Policy Binding Model Request Rule")
        verbose_name_plural = _("Policy Binding Model Request Rules")

    def __str__(self):
        return f"Policy Binding Model Request rule {self.uuid} to {self.pbm_id}"
