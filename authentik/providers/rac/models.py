"""RAC Models"""

from typing import Any
from uuid import uuid4

from deepmerge import always_merger
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest
from django.templatetags.static import static
from django.utils.translation import gettext as _
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.core.expression.exceptions import PropertyMappingExpressionException
from authentik.core.models import ExpiringModel, PropertyMapping, Provider, User, default_token_key
from authentik.events.models import Event, EventAction
from authentik.lib.models import SerializerModel
from authentik.lib.utils.time import timedelta_string_validator
from authentik.outposts.models import OutpostModel
from authentik.policies.models import PolicyBindingModel

LOGGER = get_logger()


class Protocols(models.TextChoices):
    """Supported protocols"""

    RDP = "rdp"
    VNC = "vnc"
    SSH = "ssh"


class AuthenticationMode(models.TextChoices):
    """Authentication modes"""

    STATIC = "static"
    PROMPT = "prompt"


class RACProvider(OutpostModel, Provider):
    """Remotely access computers/servers via RDP/SSH/VNC."""

    settings = models.JSONField(default=dict)
    auth_mode = models.TextField(
        choices=AuthenticationMode.choices, default=AuthenticationMode.PROMPT
    )
    connection_expiry = models.TextField(
        default="hours=8",
        validators=[timedelta_string_validator],
        help_text=_(
            "Determines how long a session lasts. Default of 0 means "
            "that the sessions lasts until the browser is closed. "
            "(Format: hours=-1;minutes=-2;seconds=-3)"
        ),
    )
    delete_token_on_disconnect = models.BooleanField(
        default=False,
        help_text=_("When set to true, connection tokens will be deleted upon disconnect."),
    )

    @property
    def launch_url(self) -> str | None:
        """URL to this provider and initiate authorization for the user.
        Can return None for providers that are not URL-based"""
        return "goauthentik.io://providers/rac/launch"

    @property
    def icon_url(self) -> str | None:
        return static("authentik/sources/rac.svg")

    @property
    def component(self) -> str:
        return "ak-provider-rac-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.rac.api.providers import RACProviderSerializer

        return RACProviderSerializer

    class Meta:
        verbose_name = _("RAC Provider")
        verbose_name_plural = _("RAC Providers")


class Endpoint(SerializerModel, PolicyBindingModel):
    """Remote-accessible endpoint"""

    name = models.TextField()
    host = models.TextField()
    protocol = models.TextField(choices=Protocols.choices)
    settings = models.JSONField(default=dict)
    auth_mode = models.TextField(choices=AuthenticationMode.choices)
    provider = models.ForeignKey("RACProvider", on_delete=models.CASCADE)
    maximum_connections = models.IntegerField(default=1)

    property_mappings = models.ManyToManyField(
        "authentik_core.PropertyMapping", default=None, blank=True
    )

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.rac.api.endpoints import EndpointSerializer

        return EndpointSerializer

    def __str__(self):
        return f"RAC Endpoint {self.name}"

    class Meta:
        verbose_name = _("RAC Endpoint")
        verbose_name_plural = _("RAC Endpoints")


class RACPropertyMapping(PropertyMapping):
    """Configure settings for remote access endpoints."""

    static_settings = models.JSONField(default=dict)

    def evaluate(self, user: User | None, request: HttpRequest | None, **kwargs) -> Any:
        """Evaluate `self.expression` using `**kwargs` as Context."""
        if len(self.static_settings) > 0:
            return self.static_settings
        return super().evaluate(user, request, **kwargs)

    @property
    def component(self) -> str:
        return "ak-property-mapping-provider-rac-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.rac.api.property_mappings import (
            RACPropertyMappingSerializer,
        )

        return RACPropertyMappingSerializer

    class Meta:
        verbose_name = _("RAC Provider Property Mapping")
        verbose_name_plural = _("RAC Provider Property Mappings")


class ConnectionToken(ExpiringModel):
    """Token for a single connection to a specified endpoint"""

    connection_token_uuid = models.UUIDField(default=uuid4, primary_key=True)
    provider = models.ForeignKey(RACProvider, on_delete=models.CASCADE)
    endpoint = models.ForeignKey(Endpoint, on_delete=models.CASCADE)
    token = models.TextField(default=default_token_key)
    settings = models.JSONField(default=dict)
    session = models.ForeignKey("authentik_core.AuthenticatedSession", on_delete=models.CASCADE)

    def get_settings(self) -> dict:
        """Get settings"""
        default_settings = {}
        if ":" in self.endpoint.host:
            host, _, port = self.endpoint.host.partition(":")
            default_settings["hostname"] = host
            default_settings["port"] = str(port)
        else:
            default_settings["hostname"] = self.endpoint.host
        if self.endpoint.protocol == Protocols.RDP:
            default_settings["resize-method"] = "display-update"
        default_settings["client-name"] = f"authentik - {self.session.user}"
        settings = {}
        always_merger.merge(settings, default_settings)
        always_merger.merge(settings, self.endpoint.provider.settings)
        always_merger.merge(settings, self.endpoint.settings)

        def mapping_evaluator(mappings: QuerySet):
            for mapping in mappings:
                mapping: RACPropertyMapping
                try:
                    mapping_settings = mapping.evaluate(
                        self.session.user, None, endpoint=self.endpoint, provider=self.provider
                    )
                    always_merger.merge(settings, mapping_settings)
                except PropertyMappingExpressionException as exc:
                    Event.new(
                        EventAction.CONFIGURATION_ERROR,
                        message=f"Failed to evaluate property-mapping: '{mapping.name}'",
                        provider=self.provider,
                        mapping=mapping,
                    ).set_user(self.session.user).save()
                    LOGGER.warning("Failed to evaluate property mapping", exc=exc)

        mapping_evaluator(
            RACPropertyMapping.objects.filter(provider__in=[self.provider]).order_by("name")
        )
        mapping_evaluator(
            RACPropertyMapping.objects.filter(endpoint__in=[self.endpoint]).order_by("name")
        )
        always_merger.merge(settings, self.settings)

        settings["drive-path"] = f"/tmp/connection/{self.token}"  # nosec
        settings["create-drive-path"] = "true"
        # Ensure all values of the settings dict are strings
        for key, value in settings.items():
            if isinstance(value, str):
                continue
            # Special case for bools
            if isinstance(value, bool):
                settings[key] = str(value).lower()
                continue
            settings[key] = str(value)
        return settings

    def __str__(self):
        return f"RAC Connection token {self.session_id} to {self.provider_id}/{self.endpoint_id}"

    class Meta:
        verbose_name = _("RAC Connection token")
        verbose_name_plural = _("RAC Connection tokens")
        indexes = ExpiringModel.Meta.indexes
