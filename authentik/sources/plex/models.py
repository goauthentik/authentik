"""Plex source"""
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import CharField
from rest_framework.serializers import BaseSerializer

from authentik.core.models import Source, UserSourceConnection
from authentik.core.types import UILoginButton
from authentik.flows.challenge import Challenge, ChallengeTypes


class PlexAuthenticationChallenge(Challenge):
    """Challenge shown to the user in identification stage"""

    client_id = CharField()
    slug = CharField()


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
            challenge=PlexAuthenticationChallenge(
                {
                    "type": ChallengeTypes.NATIVE.value,
                    "component": "ak-flow-sources-plex",
                    "client_id": self.client_id,
                    "slug": self.slug,
                }
            ),
            icon_url=static("authentik/sources/plex.svg"),
            name=self.name,
        )

    class Meta:

        verbose_name = _("Plex Source")
        verbose_name_plural = _("Plex Sources")


class PlexSourceConnection(UserSourceConnection):
    """Connect user and plex source"""

    plex_token = models.TextField()
    identifier = models.TextField()

    class Meta:

        verbose_name = _("User Plex Source Connection")
        verbose_name_plural = _("User Plex Source Connections")
