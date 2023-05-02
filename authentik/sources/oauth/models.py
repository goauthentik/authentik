"""OAuth Client models"""
from typing import TYPE_CHECKING, Optional, Type

from django.db import models
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import Source, UserSourceConnection
from authentik.core.types import UILoginButton, UserSettingSerializer

if TYPE_CHECKING:
    from authentik.sources.oauth.types.registry import SourceType


class OAuthSource(Source):
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

    @property
    def type(self) -> type["SourceType"]:
        """Return the provider instance for this source"""
        from authentik.sources.oauth.types.registry import registry

        return registry.find_type(self.provider_type)

    @property
    def component(self) -> str:
        return "ak-source-oauth-form"

    # we're using Type[] instead of type[] here since type[] interferes with the property above
    @property
    def serializer(self) -> Type[Serializer]:
        from authentik.sources.oauth.api.source import OAuthSourceSerializer

        return OAuthSourceSerializer

    def ui_login_button(self, request: HttpRequest) -> UILoginButton:
        provider_type = self.type
        provider = provider_type()
        icon = self.get_icon
        if not icon:
            icon = provider.icon_url()
        return UILoginButton(
            name=self.name,
            challenge=provider.login_challenge(self, request),
            icon_url=icon,
        )

    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        provider_type = self.type
        icon = self.get_icon
        if not icon:
            icon = provider_type().icon_url()
        return UserSettingSerializer(
            data={
                "title": self.name,
                "component": "ak-user-settings-source-oauth",
                "configure_url": reverse(
                    "authentik_sources_oauth:oauth-client-login",
                    kwargs={"source_slug": self.slug},
                ),
                "icon_url": icon,
            }
        )

    def __str__(self) -> str:
        return f"OAuth Source {self.name}"

    class Meta:
        verbose_name = _("OAuth Source")
        verbose_name_plural = _("OAuth Sources")


class GitHubOAuthSource(OAuthSource):
    """Social Login using GitHub.com or a GitHub-Enterprise Instance."""

    class Meta:
        abstract = True
        verbose_name = _("GitHub OAuth Source")
        verbose_name_plural = _("GitHub OAuth Sources")


class TwitchOAuthSource(OAuthSource):
    """Social Login using Twitch."""

    class Meta:
        abstract = True
        verbose_name = _("Twitch OAuth Source")
        verbose_name_plural = _("Twitch OAuth Sources")


class MailcowOAuthSource(OAuthSource):
    """Social Login using Mailcow."""

    class Meta:
        abstract = True
        verbose_name = _("Mailcow OAuth Source")
        verbose_name_plural = _("Mailcow OAuth Sources")


class TwitterOAuthSource(OAuthSource):
    """Social Login using Twitter.com"""

    class Meta:
        abstract = True
        verbose_name = _("Twitter OAuth Source")
        verbose_name_plural = _("Twitter OAuth Sources")


class FacebookOAuthSource(OAuthSource):
    """Social Login using Facebook.com."""

    class Meta:
        abstract = True
        verbose_name = _("Facebook OAuth Source")
        verbose_name_plural = _("Facebook OAuth Sources")


class DiscordOAuthSource(OAuthSource):
    """Social Login using Discord."""

    class Meta:
        abstract = True
        verbose_name = _("Discord OAuth Source")
        verbose_name_plural = _("Discord OAuth Sources")


class PatreonOAuthSource(OAuthSource):
    """Social Login using Patreon."""

    class Meta:
        abstract = True
        verbose_name = _("Patreon OAuth Source")
        verbose_name_plural = _("Patreon OAuth Sources")


class GoogleOAuthSource(OAuthSource):
    """Social Login using Google or Google Workspace (GSuite)."""

    class Meta:
        abstract = True
        verbose_name = _("Google OAuth Source")
        verbose_name_plural = _("Google OAuth Sources")


class AzureADOAuthSource(OAuthSource):
    """Social Login using Azure AD."""

    class Meta:
        abstract = True
        verbose_name = _("Azure AD OAuth Source")
        verbose_name_plural = _("Azure AD OAuth Sources")


class OpenIDConnectOAuthSource(OAuthSource):
    """Login using a Generic OpenID-Connect compliant provider."""

    class Meta:
        abstract = True
        verbose_name = _("OpenID OAuth Source")
        verbose_name_plural = _("OpenID OAuth Sources")


class AppleOAuthSource(OAuthSource):
    """Social Login using Apple."""

    class Meta:
        abstract = True
        verbose_name = _("Apple OAuth Source")
        verbose_name_plural = _("Apple OAuth Sources")


class OktaOAuthSource(OAuthSource):
    """Social Login using Okta."""

    class Meta:
        abstract = True
        verbose_name = _("Okta OAuth Source")
        verbose_name_plural = _("Okta OAuth Sources")


class UserOAuthSourceConnection(UserSourceConnection):
    """Authorized remote OAuth provider."""

    identifier = models.CharField(max_length=255)
    access_token = models.TextField(blank=True, null=True, default=None)

    @property
    def serializer(self) -> Serializer:
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
