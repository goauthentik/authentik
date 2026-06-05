from uuid import uuid4

from django.db import models, transaction
from rest_framework.serializers import Serializer

from authentik.core.models import CreatedUpdatedModel, ExpiringModel, User
from authentik.lib.models import SerializerModel
from authentik.policies.models import PolicyBinding, PolicyBindingModel


class Persona(User):
    # Inherited:
    #  - parent.email
    #  - parent.name (customisable)
    # Modified:
    #  - parent.username
    #  - parent.groups

    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="personas")


class Grant(ExpiringModel, CreatedUpdatedModel):
    """Grant for a persona to access `target`, given after manual/automatic approval."""

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    target = models.ForeignKey(PolicyBindingModel, on_delete=models.CASCADE)


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
    data = models.JSONField(default=dict)

    status = models.TextField(choices=RequestStatus.choices, default=RequestStatus.CREATED)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.pam.api.grant_request import GrantRequestSerializer

        return GrantRequestSerializer

    @transaction.atomic
    def fulfill(self, user: User):
        self.fulfilled_by = user
        self.save()
        if self.status != RequestStatus.APPROVED:
            return
        for target in GrantRequestTarget.objects.filter(request=self).all():
            target_binding = PolicyBinding.objects.create(
                user=self.created_by,
                target=target.target,
                expiring=self.expiring,
                expires=self.expires,
            )
            target.binding = target_binding
            target.save()


class GrantRequestTarget(models.Model):
    """Concrete m2m to make gergo happy"""

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    request = models.ForeignKey(GrantRequest, on_delete=models.CASCADE)
    binding = models.ForeignKey(PolicyBinding, on_delete=models.CASCADE, null=True)
    target = models.ForeignKey(PolicyBindingModel, on_delete=models.CASCADE)

    def __str__(self):
        return f"Grant Request-target {self.request_id} to {self.target_id}"
