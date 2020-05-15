"""OAuth Client models"""

from django.db import models
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from passbook.channels.in_oauth.clients import get_client
from passbook.core.models import Inlet, UserInletConnection
from passbook.core.types import UILoginButton, UIUserSettings


class OAuthInlet(Inlet):
    """Configuration for OAuth inlet."""

    inlet_type = models.CharField(max_length=255)
    request_token_url = models.CharField(
        blank=True, max_length=255, verbose_name=_("Request Token URL")
    )
    authorization_url = models.CharField(
        max_length=255, verbose_name=_("Authorization URL")
    )
    access_token_url = models.CharField(
        max_length=255, verbose_name=_("Access Token URL")
    )
    profile_url = models.CharField(max_length=255, verbose_name=_("Profile URL"))
    consumer_key = models.TextField()
    consumer_secret = models.TextField()

    form = "passbook.channels.in_oauth.forms.OAuthInletForm"

    @property
    def ui_login_button(self) -> UILoginButton:
        return UILoginButton(
            url=reverse_lazy(
                "passbook_channels_in_oauth:oauth-client-login",
                kwargs={"inlet_slug": self.slug},
            ),
            icon_path=f"passbook/inlets/{self.inlet_type}.svg",
            name=self.name,
        )

    @property
    def ui_additional_info(self) -> str:
        url = reverse_lazy(
            "passbook_channels_in_oauth:oauth-client-callback",
            kwargs={"inlet_slug": self.slug},
        )
        return f"Callback URL: <pre>{url}</pre>"

    @property
    def ui_user_settings(self) -> UIUserSettings:
        icon_type = self.inlet_type
        if icon_type == "azure ad":
            icon_type = "windows"
        icon_class = f"fab fa-{icon_type}"
        view_name = "passbook_channels_in_oauth:oauth-client-user"
        return UIUserSettings(
            name=self.name,
            icon=icon_class,
            view_name=reverse((view_name), kwargs={"inlet_slug": self.slug}),
        )

    class Meta:

        verbose_name = _("Generic OAuth Inlet")
        verbose_name_plural = _("Generic OAuth Inlets")


class GitHubOAuthInlet(OAuthInlet):
    """Abstract subclass of OAuthInlet to specify GitHub Form"""

    form = "passbook.channels.in_oauth.forms.GitHubOAuthInletForm"

    class Meta:

        abstract = True
        verbose_name = _("GitHub OAuth Inlet")
        verbose_name_plural = _("GitHub OAuth Inlets")


class TwitterOAuthInlet(OAuthInlet):
    """Abstract subclass of OAuthInlet to specify Twitter Form"""

    form = "passbook.channels.in_oauth.forms.TwitterOAuthInletForm"

    class Meta:

        abstract = True
        verbose_name = _("Twitter OAuth Inlet")
        verbose_name_plural = _("Twitter OAuth Inlets")


class FacebookOAuthInlet(OAuthInlet):
    """Abstract subclass of OAuthInlet to specify Facebook Form"""

    form = "passbook.channels.in_oauth.forms.FacebookOAuthInletForm"

    class Meta:

        abstract = True
        verbose_name = _("Facebook OAuth Inlet")
        verbose_name_plural = _("Facebook OAuth Inlets")


class DiscordOAuthInlet(OAuthInlet):
    """Abstract subclass of OAuthInlet to specify Discord Form"""

    form = "passbook.channels.in_oauth.forms.DiscordOAuthInletForm"

    class Meta:

        abstract = True
        verbose_name = _("Discord OAuth Inlet")
        verbose_name_plural = _("Discord OAuth Inlets")


class GoogleOAuthInlet(OAuthInlet):
    """Abstract subclass of OAuthInlet to specify Google Form"""

    form = "passbook.channels.in_oauth.forms.GoogleOAuthInletForm"

    class Meta:

        abstract = True
        verbose_name = _("Google OAuth Inlet")
        verbose_name_plural = _("Google OAuth Inlets")


class AzureADOAuthInlet(OAuthInlet):
    """Abstract subclass of OAuthInlet to specify AzureAD Form"""

    form = "passbook.channels.in_oauth.forms.AzureADOAuthInletForm"

    class Meta:

        abstract = True
        verbose_name = _("Azure AD OAuth Inlet")
        verbose_name_plural = _("Azure AD OAuth Inlets")


class UserOAuthInletConnection(UserInletConnection):
    """Authorized remote OAuth inlet."""

    identifier = models.CharField(max_length=255)
    access_token = models.TextField(blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        self.access_token = self.access_token or None
        super().save(*args, **kwargs)

    @property
    def api_client(self):
        """Get API Client"""
        return get_client(self.inlet, self.access_token or "")

    class Meta:

        verbose_name = _("User OAuth Inlet Connection")
        verbose_name_plural = _("User OAuth Inlet Connections")
