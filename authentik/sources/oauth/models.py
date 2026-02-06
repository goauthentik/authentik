"""OAuth Client models"""

from typing import TYPE_CHECKING

from django.db import models
from django.http.request import HttpRequest
from django.templatetags.static import static
from django.urls import reverse
from django.utils.timezone import now
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


class PKCEMethod(models.TextChoices):
    NONE = "none", _("No PKCE")
    PLAIN = "plain", _("Plain")
    S256 = "S256", _("S256")


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

    pkce = models.TextField(
        choices=PKCEMethod.choices, default=PKCEMethod.NONE, verbose_name=_("PKCE")
    )
    authorization_code_auth_method = models.TextField(
        choices=AuthorizationCodeAuthMethod.choices,
        default=AuthorizationCodeAuthMethod.BASIC_AUTH,
        help_text=_(
            "How to perform authentication during an authorization_code token request flow"
        ),
    )

    @property
    def source_type(self) -> type[SourceType]:
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
    def icon_themed_urls(self) -> dict[str, str] | None:
        """Get themed URLs for source icon.

        OAuth source types are abstract models so the DB always stores OAuthSource
        instances.  We resolve the built-in icon from the provider_type field instead
        of the class-level default_icon_name (which only exists on the abstract
        subclasses used by the TypeCreate wizard).
        """
        urls = super().icon_themed_urls
        if urls:
            return urls
        try:
            if self.provider_type:
                return {
                    "light": static(f"authentik/sources/{self.provider_type}/light.svg"),
                    "dark": static(f"authentik/sources/{self.provider_type}/dark.svg"),
                }
        except AttributeError:
            pass
        return None

    def ui_login_button(self, request: HttpRequest) -> UILoginButton:
        provider_type = self.source_type
        provider = provider_type()
        return UILoginButton(
            name=self.name,
            challenge=provider.login_challenge(self, request),
            icon_url=self.icon_url,
            icon_themed_urls=self.icon_themed_urls,
            promoted=self.promoted,
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
                "icon_themed_urls": self.icon_themed_urls,
            }
        )

    def __str__(self) -> str:
        return f"OAuth Source {self.name}"

    class Meta:
        verbose_name = _("OAuth Source")
        verbose_name_plural = _("OAuth Sources")


class GitHubOAuthSource(CreatableType, OAuthSource):
    """Social Login using GitHub.com or a GitHub-Enterprise Instance."""

    default_icon_name = "github"

    class Meta:
        abstract = True
        verbose_name = _("GitHub OAuth Source")
        verbose_name_plural = _("GitHub OAuth Sources")


class GitLabOAuthSource(CreatableType, OAuthSource):
    """Social Login using GitLab.com or a GitLab Instance."""

    default_icon_name = "gitlab"

    class Meta:
        abstract = True
        verbose_name = _("GitLab OAuth Source")
        verbose_name_plural = _("GitLab OAuth Sources")


class TwitchOAuthSource(CreatableType, OAuthSource):
    """Social Login using Twitch."""

    default_icon_name = "twitch"

    class Meta:
        abstract = True
        verbose_name = _("Twitch OAuth Source")
        verbose_name_plural = _("Twitch OAuth Sources")


class MailcowOAuthSource(CreatableType, OAuthSource):
    """Social Login using Mailcow."""

    default_icon_name = "mailcow"

    class Meta:
        abstract = True
        verbose_name = _("Mailcow OAuth Source")
        verbose_name_plural = _("Mailcow OAuth Sources")


class TwitterOAuthSource(CreatableType, OAuthSource):
    """Social Login using Twitter.com"""

    default_icon_name = "twitter"

    class Meta:
        abstract = True
        verbose_name = _("Twitter OAuth Source")
        verbose_name_plural = _("Twitter OAuth Sources")


class FacebookOAuthSource(CreatableType, OAuthSource):
    """Social Login using Facebook.com."""

    default_icon_name = "facebook"

    class Meta:
        abstract = True
        verbose_name = _("Facebook OAuth Source")
        verbose_name_plural = _("Facebook OAuth Sources")


class DiscordOAuthSource(CreatableType, OAuthSource):
    """Social Login using Discord."""

    default_icon_name = "discord"

    class Meta:
        abstract = True
        verbose_name = _("Discord OAuth Source")
        verbose_name_plural = _("Discord OAuth Sources")


class SlackOAuthSource(CreatableType, OAuthSource):
    """Social Login using Slack."""

    default_icon_name = "slack"

    class Meta:
        abstract = True
        verbose_name = _("Slack OAuth Source")
        verbose_name_plural = _("Slack OAuth Sources")


class PatreonOAuthSource(CreatableType, OAuthSource):
    """Social Login using Patreon."""

    default_icon_name = "patreon"

    class Meta:
        abstract = True
        verbose_name = _("Patreon OAuth Source")
        verbose_name_plural = _("Patreon OAuth Sources")


class GoogleOAuthSource(CreatableType, OAuthSource):
    """Social Login using Google or Google Workspace (GSuite)."""

    default_icon_name = "google"

    class Meta:
        abstract = True
        verbose_name = _("Google OAuth Source")
        verbose_name_plural = _("Google OAuth Sources")


class AzureADOAuthSource(CreatableType, OAuthSource):
    """(Deprecated) Social Login using Azure AD."""

    default_icon_name = "azuread"

    class Meta:
        abstract = True
        verbose_name = _("Azure AD OAuth Source")
        verbose_name_plural = _("Azure AD OAuth Sources")


# TODO: When removing this, add a migration for OAuthSource that sets
# provider_type to `entraid` if it is currently `azuread`
class EntraIDOAuthSource(CreatableType, OAuthSource):
    """Social Login using Entra ID."""

    default_icon_name = "entraid"

    class Meta:
        abstract = True
        verbose_name = _("Entra ID OAuth Source")
        verbose_name_plural = _("Entra ID OAuth Sources")


class OpenIDConnectOAuthSource(CreatableType, OAuthSource):
    """Login using a Generic OpenID-Connect compliant provider."""

    default_icon_name = "openidconnect"

    class Meta:
        abstract = True
        verbose_name = _("OpenID OAuth Source")
        verbose_name_plural = _("OpenID OAuth Sources")


class AppleOAuthSource(CreatableType, OAuthSource):
    """Social Login using Apple."""

    default_icon_name = "apple"

    class Meta:
        abstract = True
        verbose_name = _("Apple OAuth Source")
        verbose_name_plural = _("Apple OAuth Sources")


class OktaOAuthSource(CreatableType, OAuthSource):
    """Social Login using Okta."""

    default_icon_name = "okta"

    class Meta:
        abstract = True
        verbose_name = _("Okta OAuth Source")
        verbose_name_plural = _("Okta OAuth Sources")


class RedditOAuthSource(CreatableType, OAuthSource):
    """Social Login using reddit.com."""

    default_icon_name = "reddit"

    class Meta:
        abstract = True
        verbose_name = _("Reddit OAuth Source")
        verbose_name_plural = _("Reddit OAuth Sources")


class WeChatOAuthSource(CreatableType, OAuthSource):
    """Social Login using WeChat."""

    default_icon_name = "wechat"

    class Meta:
        abstract = True
        verbose_name = _("WeChat OAuth Source")
        verbose_name_plural = _("WeChat OAuth Sources")


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
    refresh_token = models.TextField(blank=True, null=True, default=None)
    expires = models.DateTimeField(default=now)

    @property
    def is_valid(self):
        return self.expires > now()

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.oauth.api.source_connection import (
            UserOAuthSourceConnectionSerializer,
        )

        return UserOAuthSourceConnectionSerializer

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
