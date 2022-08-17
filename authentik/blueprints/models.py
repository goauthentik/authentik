"""Managed Object models"""
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from requests import RequestException
from rest_framework.serializers import Serializer

from authentik.lib.config import CONFIG
from authentik.lib.models import CreatedUpdatedModel, SerializerModel
from authentik.lib.sentry import SentryIgnoredException
from authentik.lib.utils.http import get_http_session


class BlueprintRetrievalFailed(SentryIgnoredException):
    """Error raised when we're unable to fetch the blueprint contents, whether it be HTTP files
    not being accessible or local files not being readable"""


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
    status = models.TextField(
        choices=BlueprintInstanceStatus.choices, default=BlueprintInstanceStatus.UNKNOWN
    )
    enabled = models.BooleanField(default=True)
    managed_models = ArrayField(models.TextField(), default=list)

    def retrieve(self) -> str:
        """Retrieve blueprint contents"""
        if urlparse(self.path).scheme != "":
            try:
                res = get_http_session().get(self.path, timeout=3, allow_redirects=True)
                res.raise_for_status()
                return res.text
            except RequestException as exc:
                raise BlueprintRetrievalFailed(exc) from exc
        path = Path(CONFIG.y("blueprints_dir")).joinpath(Path(self.path))
        with path.open("r", encoding="utf-8") as _file:
            return _file.read()

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
