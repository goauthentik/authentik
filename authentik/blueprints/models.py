"""Managed Object models"""
from uuid import uuid4

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.lib.models import CreatedUpdatedModel, SerializerModel


class ManagedModel(models.Model):
    """Model which can be managed by authentik exclusively"""

    managed = models.TextField(
        default=None,
        null=True,
        verbose_name=_("Managed by authentik"),
        help_text=_(
            (
                "Objects which are managed by authentik. These objects are created and updated "
                "automatically. This is flag only indicates that an object can be overwritten by "
                "migrations. You can still modify the objects via the API, but expect changes "
                "to be overwritten in a later update."
            )
        ),
        unique=True,
    )

    class Meta:

        abstract = True


class BlueprintInstanceStatus(models.TextChoices):
    """Instance status"""

    SUCCESSFUL = "successful"
    WARNING = "warning"
    ERROR = "error"
    ORPHANED = "orphaned"
    UNKNOWN = "unknown"


class BlueprintInstance(SerializerModel, ManagedModel, CreatedUpdatedModel):
    """Instance of a single blueprint. Can be parameterized via context attribute when
    blueprint in `path` has inputs."""

    instance_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField()
    metadata = models.JSONField(default=dict)
    path = models.TextField()
    context = models.JSONField(default=dict)
    last_applied = models.DateTimeField(auto_now=True)
    last_applied_hash = models.TextField()
    status = models.TextField(choices=BlueprintInstanceStatus.choices)
    enabled = models.BooleanField(default=True)
    managed_models = ArrayField(models.TextField(), default=list)

    @property
    def serializer(self) -> Serializer:
        from authentik.blueprints.api import BlueprintInstanceSerializer

        return BlueprintInstanceSerializer

    def __str__(self) -> str:
        return f"Blueprint Instance {self.name}"

    class Meta:

        verbose_name = _("Blueprint Instance")
        verbose_name_plural = _("Blueprint Instances")
        unique_together = (
            (
                "name",
                "path",
            ),
        )
