"""OAuth Client models"""

from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from passbook.core.models import Source, UserSourceConnection
from passbook.oauth_client.clients import get_client


class OAuthSource(Source):
    """Configuration for OAuth provider."""

    provider_type = models.CharField(max_length=255)
    request_token_url = models.CharField(blank=True, max_length=255)
    authorization_url = models.CharField(max_length=255)
    access_token_url = models.CharField(max_length=255)
    profile_url = models.CharField(max_length=255)
    consumer_key = models.TextField()
    consumer_secret = models.TextField()

    form = 'passbook.oauth_client.forms.GitHubOAuthSourceForm'

    @property
    def is_link(self):
        return True

    @property
    def get_url(self):
        return reverse_lazy('passbook_oauth_client:oauth-client-login',
                            kwargs={'source_slug': self.slug})

    class Meta:

        verbose_name = _('Generic OAuth Source')
        verbose_name_plural = _('Generic OAuth Sources')


class GitHubOAuthSource(OAuthSource):
    """Abstract subclass of OAuthSource to specify GitHub Form"""

    form = 'passbook.oauth_client.forms.GitHubOAuthSourceForm'

    class Meta:

        abstract = True
        verbose_name = _('GitHub OAuth Source')
        verbose_name_plural = _('GitHub OAuth Sources')


class TwitterOAuthSource(OAuthSource):
    """Abstract subclass of OAuthSource to specify Twitter Form"""

    form = 'passbook.oauth_client.forms.TwitterOAuthSourceForm'

    class Meta:

        abstract = True
        verbose_name = _('Twitter OAuth Source')
        verbose_name_plural = _('Twitter OAuth Sources')


class FacebookOAuthSource(OAuthSource):
    """Abstract subclass of OAuthSource to specify Facebook Form"""

    form = 'passbook.oauth_client.forms.FacebookOAuthSourceForm'

    class Meta:

        abstract = True
        verbose_name = _('Facebook OAuth Source')
        verbose_name_plural = _('Facebook OAuth Sources')


class DiscordOAuthSource(OAuthSource):
    """Abstract subclass of OAuthSource to specify Discord Form"""

    form = 'passbook.oauth_client.forms.DiscordOAuthSourceForm'

    class Meta:

        abstract = True
        verbose_name = _('Discord OAuth Source')
        verbose_name_plural = _('Discord OAuth Sources')


class GoogleOAuthSource(OAuthSource):
    """Abstract subclass of OAuthSource to specify Google Form"""

    form = 'passbook.oauth_client.forms.GoogleOAuthSourceForm'

    class Meta:

        abstract = True
        verbose_name = _('Google OAuth Source')
        verbose_name_plural = _('Google OAuth Sources')

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
        return get_client(self.source, self.access_token or '')

    class Meta:

        verbose_name = _('User OAuth Source Connection')
        verbose_name_plural = _('User OAuth Source Connections')
