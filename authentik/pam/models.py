from uuid import uuid4

from django.db import models
from rest_framework.serializers import Serializer

from authentik.core.models import CreatedUpdatedModel, ExpiringModel, User
from authentik.lib.models import SerializerModel
from authentik.policies.models import PolicyBindingModel


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


class RequestState(models.TextChoices):
    CREATED = "created"
    APPROVED = "approved"
    DENIED = "denied"


class GrantRequest(SerializerModel, ExpiringModel, CreatedUpdatedModel):
    """Request of a user to access target(s) via Persona"""

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # Targets access was requested to
    targets = models.ManyToManyField(PolicyBindingModel, through="GrantRequestTarget")
    # Justification data, inputted by the `created_by` user via a flow, used for approve/deny
    data = models.JSONField(default=dict)

    status = models.TextField(choices=RequestState.choices, default=RequestState.CREATED)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.pam.api.grant_request import GrantRequestSerializer

        return GrantRequestSerializer


class GrantRequestTarget(models.Model):
    """Concrete m2m to make gergo happy"""

    uuid = models.UUIDField(default=uuid4, primary_key=True)

    request = models.ForeignKey(GrantRequest, on_delete=models.CASCADE)
    target = models.ForeignKey(PolicyBindingModel, on_delete=models.CASCADE)

    def __str__(self):
        return f"Grant Request-target {self.request_id} to {self.target_id}"
