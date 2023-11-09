"""RAC Models"""
from typing import Optional

from deepmerge import always_merger
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
from rest_framework.serializers import Serializer

from authentik.core.models import Provider


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
    host = models.TextField()
    settings = models.JSONField(default=dict)
    auth_mode = models.TextField(choices=AuthenticationMode.choices)

    @property
    def launch_url(self) -> Optional[str]:
        """URL to this provider and initiate authorization for the user.
        Can return None for providers that are not URL-based"""
        try:
            # pylint: disable=no-member
            return reverse(
                "authentik_providers_rac:if-rac",
                kwargs={"app": self.application.slug},
            )
        except Provider.application.RelatedObjectDoesNotExist:
            return None

    def get_settings(self) -> dict:
        """Get settings"""
        default_settings = {}
        default_settings["hostname"] = self.host
        default_settings["enable-drive"] = "true"
        default_settings["drive-name"] = "authentik"
        default_settings["client-name"] = "foo"
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
        always_merger.merge(settings, self.settings)
        return settings

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
