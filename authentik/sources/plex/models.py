"""Plex source"""

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.http.request import HttpRequest
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import CharField
from rest_framework.serializers import BaseSerializer, Serializer

from authentik.core.models import Source, UserSourceConnection
from authentik.core.types import UILoginButton, UserSettingSerializer
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    DiscriminatorField,
)
from authentik.lib.generators import generate_id


class PlexAuthenticationChallenge(Challenge):
    """Challenge shown to the user in identification stage"""

    client_id = CharField()
    slug = CharField()
    component = DiscriminatorField("ak-source-plex")


class PlexAuthenticationChallengeResponse(ChallengeResponse):
    """Pseudo class for plex response"""

    component = DiscriminatorField("ak-source-plex")


class PlexSource(Source):
    """Authenticate against plex.tv"""

    client_id = models.TextField(
        default=generate_id,
        help_text=_("Client identifier used to talk to Plex."),
    )
    allowed_servers = ArrayField(
        models.TextField(),
        default=list,
        blank=True,
        help_text=_(
            "Which servers a user has to be a member of to be granted access. "
            "Empty list allows every server."
        ),
    )
    allow_friends = models.BooleanField(
        default=True,
        help_text=_("Allow friends to authenticate, even if you don't share a server."),
    )
    plex_token = models.TextField(help_text=_("Plex token used to check friends"))

    @property
    def component(self) -> str:
        return "ak-source-plex-form"

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.sources.plex.api.source import PlexSourceSerializer

        return PlexSourceSerializer

    @property
    def icon_url(self) -> str:
        icon = super().icon_url
        if not icon:
            icon = static("authentik/sources/plex.svg")
        return icon

    def ui_login_button(self, request: HttpRequest) -> UILoginButton:
        return UILoginButton(
            challenge=PlexAuthenticationChallenge(
                data={
                    "component": "ak-source-plex",
                    "client_id": self.client_id,
                    "slug": self.slug,
                }
            ),
            icon_url=self.icon_url,
            name=self.name,
        )

    def ui_user_settings(self) -> UserSettingSerializer | None:
        return UserSettingSerializer(
            data={
                "title": self.name,
                "component": "ak-user-settings-source-plex",
                "configure_url": self.client_id,
                "icon_url": self.icon_url,
            }
        )

    class Meta:
        verbose_name = _("Plex Source")
        verbose_name_plural = _("Plex Sources")


class PlexSourceConnection(UserSourceConnection):
    """Connect user and plex source"""

    plex_token = models.TextField()
    identifier = models.TextField()

    @property
    def serializer(self) -> Serializer:
        from authentik.sources.plex.api.source_connection import PlexSourceConnectionSerializer

        return PlexSourceConnectionSerializer

    class Meta:
        verbose_name = _("User Plex Source Connection")
        verbose_name_plural = _("User Plex Source Connections")
