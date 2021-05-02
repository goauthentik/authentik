"""Plex source"""
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import BaseSerializer

from authentik.core.models import Source
from authentik.core.types import UILoginButton


class PlexSource(Source):
    """Authenticate against plex.tv"""

    client_id = models.TextField()
    allowed_servers = ArrayField(models.TextField())

    @property
    def component(self) -> str:
        return "ak-source-plex-form"

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.sources.plex.api import PlexSourceSerializer

        return PlexSourceSerializer

    @property
    def ui_login_button(self) -> UILoginButton:
        return UILoginButton(
            url="",
            icon_url=static("authentik/sources/plex.svg"),
            name=self.name,
            additional_data={
                "client_id": self.client_id,
            },
        )

    class Meta:

        verbose_name = _("Plex Source")
        verbose_name_plural = _("Plex Sources")
