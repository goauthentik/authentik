"""Plex source"""

from typing import Any

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.http.request import HttpRequest
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import CharField
from rest_framework.serializers import BaseSerializer, Serializer

from authentik.core.models import (
    GroupSourceConnection,
    PropertyMapping,
    Source,
    UserSourceConnection,
)
from authentik.core.types import UILoginButton, UserSettingSerializer
from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.lib.generators import generate_id
from authentik.lib.utils.time import fqdn_rand
from authentik.stages.identification.stage import LoginChallengeMixin
from authentik.tasks.schedules.common import ScheduleSpec
from authentik.tasks.schedules.models import ScheduledModel


class PlexAuthenticationChallenge(LoginChallengeMixin, Challenge):
    """Challenge shown to the user in identification stage"""

    client_id = CharField()
    slug = CharField()
    component = CharField(default="ak-source-plex")


class PlexAuthenticationChallengeResponse(ChallengeResponse):
    """Pseudo class for plex response"""

    component = CharField(default="ak-source-plex")


class PlexSource(ScheduledModel, Source):
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
    def property_mapping_type(self) -> type[PropertyMapping]:
        return PlexSourcePropertyMapping

    @property
    def schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.sources.plex.tasks import check_plex_token

        return [
            ScheduleSpec(
                actor=check_plex_token,
                uid=self.slug,
                args=(self.pk,),
                crontab=f"{fqdn_rand(self.pk)} */3 * * *",
            ),
        ]

    def get_base_user_properties(self, info: dict[str, Any], **kwargs):
        return {
            "username": info.get("username"),
            "email": info.get("email"),
            "name": info.get("title"),
        }

    def get_base_group_properties(self, group_id: str, **kwargs):
        return {
            "name": group_id,
        }

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


class PlexSourcePropertyMapping(PropertyMapping):
    """Map Plex properties to User of Group object attributes"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-source-plex-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.plex.api.property_mappings import PlexSourcePropertyMappingSerializer

        return PlexSourcePropertyMappingSerializer

    class Meta:
        verbose_name = _("Plex Source Property Mapping")
        verbose_name_plural = _("Plex Source Property Mappings")


class UserPlexSourceConnection(UserSourceConnection):
    """Connect user and plex source"""

    plex_token = models.TextField()

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.plex.api.source_connection import UserPlexSourceConnectionSerializer

        return UserPlexSourceConnectionSerializer

    class Meta:
        verbose_name = _("User Plex Source Connection")
        verbose_name_plural = _("User Plex Source Connections")


class GroupPlexSourceConnection(GroupSourceConnection):
    """Group-source connection"""

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.plex.api.source_connection import (
            GroupPlexSourceConnectionSerializer,
        )

        return GroupPlexSourceConnectionSerializer

    class Meta:
        verbose_name = _("Group Plex Source Connection")
        verbose_name_plural = _("Group Plex Source Connections")
