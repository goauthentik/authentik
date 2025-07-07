"""OAuth Client models"""

from typing import TYPE_CHECKING

from django.db import models
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.api.object_types import CreatableType, NonCreatableType
from authentik.core.models import (
    GroupSourceConnection,
    PropertyMapping,
    Source,
    UserSourceConnection,
)
from authentik.core.types import UILoginButton, UserSettingSerializer

if TYPE_CHECKING:
    from authentik.sources.oauth.types.registry import SourceType


class AuthorizationCodeAuthMethod(models.TextChoices):
    BASIC_AUTH = "basic_auth", _("HTTP Basic Authentication")
    POST_BODY = "post_body", _("Include the client ID and secret as request parameters")


class OAuthSource(NonCreatableType, Source):
    """Login using a Generic OAuth provider."""

    provider_type = models.CharField(max_length=255)
    request_token_url = models.CharField(
        null=True,
        max_length=255,
        verbose_name=_("Request Token URL"),
        help_text=_(
            "URL used to request the initial token. This URL is only required for OAuth 1."
        ),
    )
    authorization_url = models.CharField(
        max_length=255,
        null=True,
        verbose_name=_("Authorization URL"),
        help_text=_("URL the user is redirect to to conest the flow."),
    )
    access_token_url = models.CharField(
        max_length=255,
        null=True,
        verbose_name=_("Access Token URL"),
        help_text=_("URL used by authentik to retrieve tokens."),
    )
    profile_url = models.CharField(
        max_length=255,
        null=True,
        verbose_name=_("Profile URL"),
        help_text=_("URL used by authentik to get user information."),
    )
    additional_scopes = models.TextField(
        default="", blank=True, verbose_name=_("Additional Scopes")
    )
    consumer_key = models.TextField()
    consumer_secret = models.TextField()

    oidc_well_known_url = models.TextField(default="", blank=True)
    oidc_jwks_url = models.TextField(default="", blank=True)
    oidc_jwks = models.JSONField(default=dict, blank=True)

    authorization_code_auth_method = models.TextField(
        choices=AuthorizationCodeAuthMethod.choices,
        default=AuthorizationCodeAuthMethod.BASIC_AUTH,
        help_text=_(
            "How to perform authentication during an authorization_code token request flow"
        ),
    )

    @property
    def source_type(self) -> type["SourceType"]:
        """Return the provider instance for this source"""
        from authentik.sources.oauth.types.registry import registry

        return registry.find_type(self.provider_type)

    @property
    def component(self) -> str:
        return "ak-source-oauth-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.oauth.api.source import OAuthSourceSerializer

        return OAuthSourceSerializer

    @property
    def property_mapping_type(self) -> type[PropertyMapping]:
        return OAuthSourcePropertyMapping

    def get_base_user_properties(self, **kwargs):
        return self.source_type().get_base_user_properties(source=self, **kwargs)

    def get_base_group_properties(self, **kwargs):
        return self.source_type().get_base_group_properties(source=self, **kwargs)

    @property
    def icon_url(self) -> str | None:
        # When listing source types, this property might be retrieved from an abstract
        # model. In that case we can't check self.provider_type or self.icon_url
        # and as such we attempt to find the correct provider type based on the mode name
        if self.Meta.abstract:
            from authentik.sources.oauth.types.registry import registry

            provider_type = registry.find_type(
                self._meta.model_name.replace(OAuthSource._meta.model_name, "")
            )
            return provider_type().icon_url()
        icon = super().icon_url
        if not icon:
            provider_type = self.source_type
            provider = provider_type()
            icon = provider.icon_url()
        return icon

    def ui_login_button(self, request: HttpRequest) -> UILoginButton:
        provider_type = self.source_type
        provider = provider_type()
        return UILoginButton(
            name=self.name,
            challenge=provider.login_challenge(self, request),
            icon_url=self.icon_url,
        )

    def ui_user_settings(self) -> UserSettingSerializer | None:
        return UserSettingSerializer(
            data={
                "title": self.name,
                "component": "ak-user-settings-source-oauth",
                "configure_url": reverse(
                    "authentik_sources_oauth:oauth-client-login",
                    kwargs={"source_slug": self.slug},
                ),
                "icon_url": self.icon_url,
            }
        )

    def __str__(self) -> str:
        return f"OAuth Source {self.name}"

    class Meta:
        verbose_name = _("OAuth Source")
        verbose_name_plural = _("OAuth Sources")


class GitHubOAuthSource(CreatableType, OAuthSource):
    """Social Login using GitHub.com or a GitHub-Enterprise Instance."""

    class Meta:
        abstract = True
        verbose_name = _("GitHub OAuth Source")
        verbose_name_plural = _("GitHub OAuth Sources")


class GitLabOAuthSource(CreatableType, OAuthSource):
    """Social Login using GitLab.com or a GitLab Instance."""

    class Meta:
        abstract = True
        verbose_name = _("GitLab OAuth Source")
        verbose_name_plural = _("GitLab OAuth Sources")


class TwitchOAuthSource(CreatableType, OAuthSource):
    """Social Login using Twitch."""

    class Meta:
        abstract = True
        verbose_name = _("Twitch OAuth Source")
        verbose_name_plural = _("Twitch OAuth Sources")


class MailcowOAuthSource(CreatableType, OAuthSource):
    """Social Login using Mailcow."""

    class Meta:
        abstract = True
        verbose_name = _("Mailcow OAuth Source")
        verbose_name_plural = _("Mailcow OAuth Sources")


class TwitterOAuthSource(CreatableType, OAuthSource):
    """Social Login using Twitter.com"""

    class Meta:
        abstract = True
        verbose_name = _("Twitter OAuth Source")
        verbose_name_plural = _("Twitter OAuth Sources")


class FacebookOAuthSource(CreatableType, OAuthSource):
    """Social Login using Facebook.com."""

    class Meta:
        abstract = True
        verbose_name = _("Facebook OAuth Source")
        verbose_name_plural = _("Facebook OAuth Sources")


class DiscordOAuthSource(CreatableType, OAuthSource):
    """Social Login using Discord."""

    class Meta:
        abstract = True
        verbose_name = _("Discord OAuth Source")
        verbose_name_plural = _("Discord OAuth Sources")


class PatreonOAuthSource(CreatableType, OAuthSource):
    """Social Login using Patreon."""

    class Meta:
        abstract = True
        verbose_name = _("Patreon OAuth Source")
        verbose_name_plural = _("Patreon OAuth Sources")


class GoogleOAuthSource(CreatableType, OAuthSource):
    """Social Login using Google or Google Workspace (GSuite)."""

    class Meta:
        abstract = True
        verbose_name = _("Google OAuth Source")
        verbose_name_plural = _("Google OAuth Sources")


class AzureADOAuthSource(CreatableType, OAuthSource):
    """Social Login using Azure AD."""

    class Meta:
        abstract = True
        verbose_name = _("Azure AD OAuth Source")
        verbose_name_plural = _("Azure AD OAuth Sources")


class OpenIDConnectOAuthSource(CreatableType, OAuthSource):
    """Login using a Generic OpenID-Connect compliant provider."""

    class Meta:
        abstract = True
        verbose_name = _("OpenID OAuth Source")
        verbose_name_plural = _("OpenID OAuth Sources")


class AppleOAuthSource(CreatableType, OAuthSource):
    """Social Login using Apple."""

    class Meta:
        abstract = True
        verbose_name = _("Apple OAuth Source")
        verbose_name_plural = _("Apple OAuth Sources")


class OktaOAuthSource(CreatableType, OAuthSource):
    """Social Login using Okta."""

    class Meta:
        abstract = True
        verbose_name = _("Okta OAuth Source")
        verbose_name_plural = _("Okta OAuth Sources")


class RedditOAuthSource(CreatableType, OAuthSource):
    """Social Login using reddit.com."""

    class Meta:
        abstract = True
        verbose_name = _("Reddit OAuth Source")
        verbose_name_plural = _("Reddit OAuth Sources")


class OAuthSourcePropertyMapping(PropertyMapping):
    """Map OAuth properties to User or Group object attributes"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-source-oauth-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.oauth.api.property_mappings import (
            OAuthSourcePropertyMappingSerializer,
        )

        return OAuthSourcePropertyMappingSerializer

    class Meta:
        verbose_name = _("OAuth Source Property Mapping")
        verbose_name_plural = _("OAuth Source Property Mappings")


class UserOAuthSourceConnection(UserSourceConnection):
    """Authorized remote OAuth provider."""

    access_token = models.TextField(blank=True, null=True, default=None)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.oauth.api.source_connection import (
            UserOAuthSourceConnectionSerializer,
        )

        return UserOAuthSourceConnectionSerializer

    def save(self, *args, **kwargs):
        self.access_token = self.access_token or None
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("User OAuth Source Connection")
        verbose_name_plural = _("User OAuth Source Connections")


class GroupOAuthSourceConnection(GroupSourceConnection):
    """Group-source connection"""

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.oauth.api.source_connection import (
            GroupOAuthSourceConnectionSerializer,
        )

        return GroupOAuthSourceConnectionSerializer

    class Meta:
        verbose_name = _("Group OAuth Source Connection")
        verbose_name_plural = _("Group OAuth Source Connections")
