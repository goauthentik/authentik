"""OAuth Client models"""
from typing import TYPE_CHECKING, Optional, Type

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import Source, UserSourceConnection
from authentik.core.types import UILoginButton, UserSettingSerializer
from authentik.flows.challenge import ChallengeTypes, RedirectChallenge

if TYPE_CHECKING:
    from authentik.sources.oauth.types.manager import SourceType


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
    consumer_key = models.TextField()
    consumer_secret = models.TextField()

    @property
    def type(self) -> Type["SourceType"]:
        """Return the provider instance for this source"""
        from authentik.sources.oauth.types.manager import MANAGER

        return MANAGER.find_type(self.provider_type)

    @property
    def component(self) -> str:
        return "ak-source-oauth-form"

    @property
    def serializer(self) -> Type[Serializer]:
        from authentik.sources.oauth.api.source import OAuthSourceSerializer

        return OAuthSourceSerializer

    @property
    def ui_login_button(self) -> UILoginButton:
        provider_type = self.type
        return UILoginButton(
            challenge=RedirectChallenge(
                instance={
                    "type": ChallengeTypes.REDIRECT.value,
                    "to": reverse(
                        "authentik_sources_oauth:oauth-client-login",
                        kwargs={"source_slug": self.slug},
                    ),
                }
            ),
            icon_url=provider_type().icon_url(),
            name=self.name,
        )

    @property
    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        return UserSettingSerializer(
            data={
                "title": f"OAuth {self.name}",
                "component": "ak-user-settings-source-oauth",
                "configure_url": reverse(
                    "authentik_sources_oauth:oauth-client-login",
                    kwargs={"source_slug": self.slug},
                ),
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


class GoogleOAuthSource(OAuthSource):
    """Social Login using Google or Gsuite."""

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
    """Login using a apple.com."""

    class Meta:

        abstract = True
        verbose_name = _("Apple OAuth Source")
        verbose_name_plural = _("Apple OAuth Sources")


class UserOAuthSourceConnection(UserSourceConnection):
    """Authorized remote OAuth provider."""

    identifier = models.CharField(max_length=255)
    access_token = models.TextField(blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        self.access_token = self.access_token or None
        super().save(*args, **kwargs)

    class Meta:

        verbose_name = _("User OAuth Source Connection")
        verbose_name_plural = _("User OAuth Source Connections")
