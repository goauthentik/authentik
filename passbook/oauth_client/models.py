"""OAuth Client models"""

from django.db import models

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

    form = 'passbook.oauth_client.forms.OAuthSourceForm'

    class Meta:

        verbose_name = 'OAuth Source'
        verbose_name_plural = 'OAuth Sources'


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

        verbose_name = 'User OAuth Source Connection'
        verbose_name_plural = 'User OAuth Source Connections'
