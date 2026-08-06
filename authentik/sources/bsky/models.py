from typing import Any

from django.db import models
from django.http.request import HttpRequest
from django.templatetags.static import static
from django.urls import reverse
from django.utils.timezone import now
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
from authentik.sources.bsky.keys import generate_bsky_signing_key
from authentik.stages.identification.stage import LoginChallengeMixin


class BskyAuthenticationChallenge(LoginChallengeMixin, Challenge):
    """Challenge shown to the user in identification stage"""

    slug = CharField()
    component = CharField(default="ak-source-bsky")


class BskyAuthenticationChallengeResult(ChallengeResponse):
    """Pseudo class for bsky response"""

    handle = CharField()
    component = CharField(default="ak-source-bsky")


class BskySource(Source):
    """Social Login with Bluesky"""

    signing_key = models.TextField(default=generate_bsky_signing_key)
    scope = models.TextField(default="atproto transition:generic")

    def client_id(self, request: HttpRequest) -> str:
        """atproto client id is a url pointing to public client metadata"""

        return request.build_absolute_uri(
            reverse(
                "authentik_sources_bsky:oauth-client-metadata", kwargs={"source_slug": self.slug}
            )
        )

    @property
    def component(self) -> str:
        return "ak-source-bsky-form"

    @property
    def serializer(self) -> type[BaseSerializer[Any]]:
        from authentik.sources.bsky.api.source import BskySourceSerializer

        return BskySourceSerializer

    @property
    def property_mapping_type(self) -> type[PropertyMapping]:
        return BskySourcePropertyMapping

    def get_base_user_properties(self, **kwargs: Any) -> dict[str, Any | dict[str, Any]]:
        info: dict[str, Any] = kwargs.get("info", {})
        return {
            "username": info.get("handle"),
            "name": info.get("displayName") or info.get("handle"),
        }

    @property
    def icon_url(self) -> str | None:
        icon = super().icon_url
        if not icon:
            icon = static("authentik/sources/bsky.svg")
        return icon

    def ui_login_button(self, request: HttpRequest) -> UILoginButton | None:
        return UILoginButton(
            challenge=BskyAuthenticationChallenge(
                data={"component": "ak-source-bsky", "slug": self.slug},
            ),
            name=self.name,
            icon_url=self.get_icon_url(request, use_cache=False) or self.icon_url,
            promoted=self.promoted,
        )

    def ui_user_settings(self) -> UserSettingSerializer | None:
        return UserSettingSerializer(
            data={
                "title": self.name,
                "component": "ak-user-settings-source-bsky",
                "configure_url": reverse(
                    "authentik_sources_bsky:oauth-client-login", kwargs={"source_slug": self.slug}
                ),
                "icon_url": self.icon_url,
            }
        )

    class Meta:
        verbose_name = _("Bluesky OAuth Source")
        verbose_name_plural = _("Bluesky OAuth Sources")


class BskySourcePropertyMapping(PropertyMapping):
    """Map Bluesky properties to User of Group object attributes"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-source-bsky-form"

    @property
    def serializer(self) -> type[Serializer[Any]]:
        from authentik.sources.bsky.api.property_mappings import BskySourcePropertyMappingSerializer

        return BskySourcePropertyMappingSerializer


class UserBskySourceConnection(UserSourceConnection):
    """Connect user and bsky source"""

    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True, default=None)
    expires = models.DateTimeField(default=now)

    @property
    def is_valid(self) -> bool:
        return self.expires > now()

    @property
    def serializer(self) -> type[Serializer[Any]]:
        from authentik.sources.bsky.api.source_connection import UserBskySourceConnectionSerializer

        return UserBskySourceConnectionSerializer

    class Meta:
        verbose_name = _("User Bluesky Source Connection")
        verbose_name_plural = _("User Bluesky Source Connections")


class GroupBskySourceConnection(GroupSourceConnection):
    """Group-source connection"""

    @property
    def serializer(self) -> type[Serializer[Any]]:
        from authentik.sources.bsky.api.source_connection import GroupBskySourceConnectionSerializer

        return GroupBskySourceConnectionSerializer

    class Meta:
        verbose_name = _("Group Bluesky Source Connection")
        verbose_name_plural = _("Group Bluesky Source Connections")
