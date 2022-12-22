"""blueprint models"""
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from opencontainers.distribution.reggie import (
    NewClient,
    WithDebug,
    WithDefaultName,
    WithDigest,
    WithReference,
    WithUserAgent,
    WithUsernamePassword,
)
from requests.exceptions import RequestException
from rest_framework.serializers import Serializer
from structlog import get_logger

from authentik.lib.config import CONFIG
from authentik.lib.models import CreatedUpdatedModel, SerializerModel
from authentik.lib.sentry import SentryIgnoredException
from authentik.lib.utils.http import authentik_user_agent

OCI_MEDIA_TYPE = "application/vnd.goauthentik.blueprint.v1+yaml"
LOGGER = get_logger()


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

    def retrieve_oci(self) -> str:
        """Get blueprint from an OCI registry"""
        url = urlparse(self.path)
        ref = "latest"
        path = url.path[1:]
        if ":" in url.path:
            path, _, ref = path.partition(":")
        client = NewClient(
            f"https://{url.hostname}",
            WithUserAgent(authentik_user_agent()),
            WithUsernamePassword(url.username, url.password),
            WithDefaultName(path),
            WithDebug(True),
        )
        LOGGER.info("Fetching OCI manifests for blueprint", instance=self)
        manifest_request = client.NewRequest(
            "GET",
            "/v2/<name>/manifests/<reference>",
            WithReference(ref),
        ).SetHeader("Accept", "application/vnd.oci.image.manifest.v1+json")
        try:
            manifest_response = client.Do(manifest_request)
            manifest_response.raise_for_status()
        except RequestException as exc:
            raise BlueprintRetrievalFailed(exc) from exc
        manifest = manifest_response.json()
        if "errors" in manifest:
            raise BlueprintRetrievalFailed(manifest["errors"])

        blob = None
        for layer in manifest.get("layers", []):
            if layer.get("mediaType", "") == OCI_MEDIA_TYPE:
                blob = layer.get("digest")
                LOGGER.debug("Found layer with matching media type", instance=self, blob=blob)
        if not blob:
            raise BlueprintRetrievalFailed("Blob not found")

        blob_request = client.NewRequest(
            "GET",
            "/v2/<name>/blobs/<digest>",
            WithDigest(blob),
        )
        try:
            blob_response = client.Do(blob_request)
            blob_response.raise_for_status()
            return blob_response.text
        except RequestException as exc:
            raise BlueprintRetrievalFailed(exc) from exc

    def retrieve(self) -> str:
        """Retrieve blueprint contents"""
        if self.path.startswith("oci://"):
            return self.retrieve_oci()
        full_path = Path(CONFIG.y("blueprints_dir")).joinpath(Path(self.path))
        with full_path.open("r", encoding="utf-8") as _file:
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
