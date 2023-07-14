"""blueprint models"""
from pathlib import Path
from uuid import uuid4

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer
from structlog import get_logger

from authentik.blueprints.v1.oci import OCI_PREFIX, BlueprintOCIClient, OCIException
from authentik.lib.config import CONFIG
from authentik.lib.models import CreatedUpdatedModel, SerializerModel
from authentik.lib.sentry import SentryIgnoredException

LOGGER = get_logger()


class BlueprintRetrievalFailed(SentryIgnoredException):
    """Error raised when we are unable to fetch the blueprint contents, whether it be HTTP files
    not being accessible or local files not being readable"""


class ManagedModel(models.Model):
    """Model that can be managed by authentik exclusively"""

    managed = models.TextField(
        default=None,
        null=True,
        verbose_name=_("Managed by authentik"),
        help_text=_(
            "Objects that are managed by authentik. These objects are created and updated "
            "automatically. This flag only indicates that an object can be overwritten by "
            "migrations. You can still modify the objects via the API, but expect changes "
            "to be overwritten in a later update."
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

    name = models.TextField(unique=True)
    metadata = models.JSONField(default=dict)
    path = models.TextField(default="", blank=True)
    content = models.TextField(default="", blank=True)
    context = models.JSONField(default=dict)
    last_applied = models.DateTimeField(auto_now=True)
    last_applied_hash = models.TextField()
    status = models.TextField(
        choices=BlueprintInstanceStatus.choices, default=BlueprintInstanceStatus.UNKNOWN
    )
    enabled = models.BooleanField(default=True)
    managed_models = ArrayField(models.TextField(), default=list)

    def retrieve_oci(self) -> str:
        """Get blueprint from an OCI registry"""
        client = BlueprintOCIClient(self.path.replace(OCI_PREFIX, "https://"))
        try:
            manifests = client.fetch_manifests()
            return client.fetch_blobs(manifests)
        except OCIException as exc:
            raise BlueprintRetrievalFailed(exc) from exc

    def retrieve_file(self) -> str:
        """Get blueprint from path"""
        try:
            base = Path(CONFIG.y("blueprints_dir"))
            full_path = base.joinpath(Path(self.path)).resolve()
            if not str(full_path).startswith(str(base.resolve())):
                raise BlueprintRetrievalFailed("Invalid blueprint path")
            with full_path.open("r", encoding="utf-8") as _file:
                return _file.read()
        except (IOError, OSError) as exc:
            raise BlueprintRetrievalFailed(exc) from exc

    def retrieve(self) -> str:
        """Retrieve blueprint contents"""
        if self.path.startswith(OCI_PREFIX):
            return self.retrieve_oci()
        if self.path != "":
            return self.retrieve_file()
        return self.content

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
