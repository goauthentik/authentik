"""RAC Models"""
from typing import Optional
from uuid import uuid4

from deepmerge import always_merger
from django.db import models
from django.utils.translation import gettext as _
from rest_framework.serializers import Serializer

from authentik.core.models import ExpiringModel, PropertyMapping, Provider, default_token_key
from authentik.lib.models import SerializerModel
from authentik.policies.models import PolicyBindingModel


class Protocols(models.TextChoices):
    """Supported protocols"""

    RDP = "rdp"
    VNC = "vnc"
    SSH = "ssh"


class AuthenticationMode(models.TextChoices):
    """Authentication modes"""

    STATIC = "static"
    PROMPT = "prompt"


class RACProvider(Provider):
    """Remote access provider"""

    protocol = models.TextField(choices=Protocols.choices)
    settings = models.JSONField(default=dict)
    auth_mode = models.TextField(choices=AuthenticationMode.choices)

    @property
    def launch_url(self) -> Optional[str]:
        """URL to this provider and initiate authorization for the user.
        Can return None for providers that are not URL-based"""
        return "goauthentik.io://providers/rac/launch"

    @property
    def component(self) -> str:
        return "ak-provider-rac-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.rac.api.providers import RACProviderSerializer

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

    property_mappings = models.ManyToManyField(
        "authentik_core.PropertyMapping", default=None, blank=True
    )

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.rac.api.endpoints import EndpointSerializer

        return EndpointSerializer

    def __str__(self):
        return f"RAC Endpoint {self.name}"

    class Meta:
        verbose_name = _("RAC Endpoint")
        verbose_name_plural = _("RAC Endpoints")


class RACPropertyMapping(PropertyMapping):
    """RAC Property mapping"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-rac-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.rac.api.property_mappings import (
            PropertyMappingSerializer,
        )

        return PropertyMappingSerializer

    class Meta:
        verbose_name = _("RAC Property Mapping")
        verbose_name_plural = _("RAC Property Mappings")


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
        default_settings["client-name"] = "authentik"
        # default_settings["enable-drive"] = "true"
        # default_settings["drive-name"] = "authentik"
        if self.endpoint.protocol == Protocols.RDP:
            default_settings["resize-method"] = "display-update"
            default_settings["enable-wallpaper"] = "true"
            default_settings["enable-font-smoothing"] = "true"
            # params["enable-theming"] = "true"
            # params["enable-full-window-drag"] = "true"
            # params["enable-desktop-composition"] = "true"
            # params["enable-menu-animations"] = "true"
            # params["enable-audio-input"] = "true"
        if self.endpoint.protocol == Protocols.SSH:
            default_settings["terminal-type"] = "xterm-256color"
        settings = {}
        always_merger.merge(settings, default_settings)
        always_merger.merge(settings, self.endpoint.provider.settings)
        always_merger.merge(settings, self.endpoint.settings)
        always_merger.merge(settings, self.settings)
        return settings
