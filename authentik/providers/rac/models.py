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
from authentik.core.models import PropertyMapping, Provider, User, default_token_key
from authentik.endpoints.connectors.agent.controller import AgentConnectorController
from authentik.endpoints.models import Device
from authentik.events.models import Event, EventAction
from authentik.lib.models import ExpiringModel, InternallyManagedMixin
from authentik.lib.utils.time import timedelta_string_validator
from authentik.outposts.models import OutpostModel

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


def connection_override(device: Device) -> RACConnectionOverride | None:
    """Connection override of a device, if it has one"""
    return getattr(device, "rac_override", None)


def available_protocols(device: Device) -> list[str]:
    """Protocols a device can be connected to with. Set explicitly by a connection
    override, otherwise based on what the device reports. Devices which report neither
    can be connected to with either protocol, as there is nothing that says they
    can't."""
    if override := connection_override(device):
        return [override.protocol]
    vendor = (device.facts_data.get("vendor") or {}).get(
        AgentConnectorController.vendor_identifier()
    ) or {}
    protocols = []
    if vendor.get("rdp_cert_fingerprint"):
        protocols.append(Protocols.RDP)
    if vendor.get("ssh_host_keys"):
        protocols.append(Protocols.SSH)
    return protocols or [Protocols.RDP, Protocols.SSH]


def address_settings(device: Device) -> dict[str, str]:
    """Hostname and port to connect to a device on. Set explicitly for devices which
    are not enrolled, otherwise taken from the facts the device reported."""
    override = connection_override(device)
    address = override.host if override else device.address
    if not address:
        return {}
    # An IPv6 address with a port is bracketed: [2001:db8::1]:3389
    if address.startswith("[") and "]:" in address:
        host, _, port = address.partition("]:")
        return {"hostname": host[1:], "port": port}
    host, _, port = address.rpartition(":")
    # Any other colon belongs to an IPv6 address, not to a port
    if host and ":" not in host and port.isdigit():
        return {"hostname": host, "port": port}
    return {"hostname": address}


class RACProvider(OutpostModel, Provider):
    """Remotely access devices via RDP/SSH/VNC."""

    settings = models.JSONField(default=dict)
    access_group = models.ForeignKey(
        "authentik_endpoints.DeviceAccessGroup",
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_DEFAULT,
        help_text=_(
            "Only devices in this access group can be accessed through this provider. "
            "When left empty, every device the user has access to can be accessed."
        ),
    )
    maximum_connections = models.IntegerField(
        default=1,
        help_text=_(
            "Maximum concurrent connections to a single device. Can be set to -1 to "
            "disable the limit."
        ),
    )
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

    def devices(self) -> QuerySet[Device]:
        """All devices this provider can connect to, before policies are checked"""
        devices = Device.objects.all()
        if self.access_group_id:
            devices = devices.filter(access_group=self.access_group_id)
        return devices

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


class RACPropertyMapping(PropertyMapping):
    """Configure settings for remote access to devices."""

    static_settings = models.JSONField(default=dict)

    def evaluate(self, user: User | None, request: HttpRequest | None, **kwargs) -> Any:
        """Evaluate `self.expression` using `**kwargs` as Context."""
        settings = {}
        for key, value in self.static_settings.items():
            if value and value != "":
                settings[key] = value
        if self.expression != "":
            always_merger.merge(settings, super().evaluate(user, request, **kwargs))
        return settings

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


class RACConnectionOverride(InternallyManagedMixin, models.Model):
    """How to reach a single device, for devices which don't report an address and
    protocol themselves."""

    device = models.OneToOneField(
        "authentik_endpoints.Device",
        on_delete=models.CASCADE,
        related_name="rac_override",
    )
    host = models.TextField(help_text=_("Hostname/IP to connect to. Optionally specify the port."))
    protocol = models.TextField(choices=Protocols.choices)

    class Meta:
        verbose_name = _("RAC Connection override")
        verbose_name_plural = _("RAC Connection overrides")

    def __str__(self):
        return f"RAC Connection override for device {self.device_id}"


class ConnectionToken(InternallyManagedMixin, ExpiringModel):
    """Token for a single connection to a device"""

    connection_token_uuid = models.UUIDField(default=uuid4, primary_key=True)
    provider = models.ForeignKey(RACProvider, on_delete=models.CASCADE)
    device = models.ForeignKey("authentik_endpoints.Device", on_delete=models.CASCADE)
    protocol = models.TextField(choices=Protocols.choices)
    token = models.TextField(default=default_token_key)
    settings = models.JSONField(default=dict)
    session = models.ForeignKey("authentik_core.AuthenticatedSession", on_delete=models.CASCADE)

    def get_settings(self) -> dict:
        """Get settings"""
        settings = {}
        if self.protocol == Protocols.RDP:
            settings["resize-method"] = "display-update"
        settings["client-name"] = f"authentik - {self.session.user}"
        always_merger.merge(settings, self.provider.settings)
        always_merger.merge(settings, address_settings(self.device))

        def mapping_evaluator(mappings: QuerySet):
            for mapping in mappings:
                mapping: RACPropertyMapping
                try:
                    mapping_settings = mapping.evaluate(
                        self.session.user, None, device=self.device, provider=self.provider
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
        return f"RAC Connection token {self.session_id} to {self.provider_id}/{self.device_id}"

    class Meta:
        verbose_name = _("RAC Connection token")
        verbose_name_plural = _("RAC Connection tokens")
        indexes = ExpiringModel.Meta.indexes
