"""RAC Models"""
from typing import Optional

from deepmerge import always_merger
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
from rest_framework.serializers import Serializer

from authentik.core.models import PropertyMapping, Provider
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
    endpoints = models.ManyToManyField("Endpoint", blank=True)

    @property
    def launch_url(self) -> Optional[str]:
        """URL to this provider and initiate authorization for the user.
        Can return None for providers that are not URL-based"""
        if len(self.endpoints.all()) < 1:
            return None
        try:
            # pylint: disable=no-member
            return reverse(
                "authentik_providers_rac:if-rac",
                kwargs={"app": self.application.slug},
            )
        except Provider.application.RelatedObjectDoesNotExist:
            return None

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

    property_mappings = models.ManyToManyField(
        "authentik_core.PropertyMapping", default=None, blank=True
    )

    def get_settings(self, provider: RACProvider) -> dict:
        """Get settings"""
        default_settings = {}
        default_settings["hostname"] = self.host
        # default_settings["enable-drive"] = "true"
        # default_settings["drive-name"] = "authentik"
        # default_settings["client-name"] = "foo"
        if self.protocol == Protocols.RDP:
            default_settings["resize-method"] = "display-update"
            default_settings["enable-wallpaper"] = "true"
            default_settings["enable-font-smoothing"] = "true"
            # params["enable-theming"] = "true"
            # params["enable-full-window-drag"] = "true"
            # params["enable-desktop-composition"] = "true"
            # params["enable-menu-animations"] = "true"
            # params["enable-audio-input"] = "true"
        if self.protocol == Protocols.SSH:
            default_settings["terminal-type"] = "xterm-256color"
        settings = {}
        always_merger.merge(settings, default_settings)
        always_merger.merge(settings, provider.settings)
        always_merger.merge(settings, self.settings)
        return settings

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.rac.api.endpoints import EndpointSerializer

        return EndpointSerializer

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
