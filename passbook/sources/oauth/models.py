"""OAuth Client models"""

from django.db import models
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Source, UserSourceConnection
from passbook.core.types import UILoginButton, UIUserSettings
from passbook.sources.oauth.clients import get_client


class OAuthSource(Source):
    """Configuration for OAuth provider."""

    provider_type = models.CharField(max_length=255)
    request_token_url = models.CharField(
        blank=True, max_length=255, verbose_name=_("Request Token URL"),
        help_text=_("URL used to request the initial token. This URL is only required for OAuth 1.")
    )
    authorization_url = models.CharField(
        max_length=255, verbose_name=_("Authorization URL"),
        help_text=_("URL the user is redirect to to conest the flow.")
    )
    access_token_url = models.CharField(
        max_length=255, verbose_name=_("Access Token URL"),
        help_text=_("URL used by passbook to retrive tokens.")
    )
    profile_url = models.CharField(
        max_length=255, verbose_name=_("Profile URL"),
        help_text=_("URL used by passbook to get user information."))
    consumer_key = models.TextField()
    consumer_secret = models.TextField()

    form = "passbook.sources.oauth.forms.OAuthSourceForm"

    @property
    def ui_login_button(self) -> UILoginButton:
        return UILoginButton(
            url=reverse_lazy(
                "passbook_sources_oauth:oauth-client-login",
                kwargs={"source_slug": self.slug},
            ),
            icon_path=f"passbook/sources/{self.provider_type}.svg",
            name=self.name,
        )

    @property
    def ui_additional_info(self) -> str:
        url = reverse_lazy(
            "passbook_sources_oauth:oauth-client-callback",
            kwargs={"source_slug": self.slug},
        )
        return f"Callback URL: <pre>{url}</pre>"

    @property
    def ui_user_settings(self) -> UIUserSettings:
        icon_type = self.provider_type
        if icon_type == "azure ad":
            icon_type = "windows"
        icon_class = f"fab fa-{icon_type}"
        view_name = "passbook_sources_oauth:oauth-client-user"
        return UIUserSettings(
            name=self.name,
            icon=icon_class,
            view_name=reverse((view_name), kwargs={"source_slug": self.slug}),
        )

    def __str__(self) -> str:
        return f"OAuth Source {self.name}"

    class Meta:

        verbose_name = _("Generic OAuth Source")
        verbose_name_plural = _("Generic OAuth Sources")


class GitHubOAuthSource(OAuthSource):
    """Abstract subclass of OAuthSource to specify GitHub Form"""

    form = "passbook.sources.oauth.forms.GitHubOAuthSourceForm"

    class Meta:

        abstract = True
        verbose_name = _("GitHub OAuth Source")
        verbose_name_plural = _("GitHub OAuth Sources")


class TwitterOAuthSource(OAuthSource):
    """Abstract subclass of OAuthSource to specify Twitter Form"""

    form = "passbook.sources.oauth.forms.TwitterOAuthSourceForm"

    class Meta:

        abstract = True
        verbose_name = _("Twitter OAuth Source")
        verbose_name_plural = _("Twitter OAuth Sources")


class FacebookOAuthSource(OAuthSource):
    """Abstract subclass of OAuthSource to specify Facebook Form"""

    form = "passbook.sources.oauth.forms.FacebookOAuthSourceForm"

    class Meta:

        abstract = True
        verbose_name = _("Facebook OAuth Source")
        verbose_name_plural = _("Facebook OAuth Sources")


class DiscordOAuthSource(OAuthSource):
    """Abstract subclass of OAuthSource to specify Discord Form"""

    form = "passbook.sources.oauth.forms.DiscordOAuthSourceForm"

    class Meta:

        abstract = True
        verbose_name = _("Discord OAuth Source")
        verbose_name_plural = _("Discord OAuth Sources")


class GoogleOAuthSource(OAuthSource):
    """Abstract subclass of OAuthSource to specify Google Form"""

    form = "passbook.sources.oauth.forms.GoogleOAuthSourceForm"

    class Meta:

        abstract = True
        verbose_name = _("Google OAuth Source")
        verbose_name_plural = _("Google OAuth Sources")


class AzureADOAuthSource(OAuthSource):
    """Abstract subclass of OAuthSource to specify AzureAD Form"""

    form = "passbook.sources.oauth.forms.AzureADOAuthSourceForm"

    class Meta:

        abstract = True
        verbose_name = _("Azure AD OAuth Source")
        verbose_name_plural = _("Azure AD OAuth Sources")

class OpenIDOAuthSource(OAuthSource):
    """Abstract subclass of OAuthSource to specify OpenID Form"""

    form = "passbook.sources.oauth.forms.OAuthSourceForm"

    class Meta:

        abstract = True
        verbose_name = _("OpenID OAuth Source")
        verbose_name_plural = _("OpenID OAuth Sources")


class UserOAuthSourceConnection(UserSourceConnection):
    """Authorized remote OAuth provider."""

    identifier = models.CharField(max_length=255)
    access_token = models.TextField(blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        self.access_token = self.access_token or None
        super().save(*args, **kwargs)

    @property
    def api_client(self):
        """Get API Client"""
        return get_client(self.source, self.access_token or "")

    class Meta:

        verbose_name = _("User OAuth Source Connection")
        verbose_name_plural = _("User OAuth Source Connections")
