"""passbook oauth_client forms"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext as _

from passbook.admin.forms.source import SOURCE_FORM_FIELDS
from passbook.oauth_client.models import OAuthSource
from passbook.oauth_client.source_types.manager import MANAGER


class OAuthSourceForm(forms.ModelForm):
    """OAuthSource Form"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self.Meta, 'overrides'):
            for overide_field, overide_value in getattr(self.Meta, 'overrides').items():
                self.fields[overide_field].initial = overide_value
                self.fields[overide_field].widget.attrs['readonly'] = 'readonly'

    class Meta:

        model = OAuthSource
        fields = SOURCE_FORM_FIELDS + ['provider_type', 'request_token_url', 'authorization_url',
                                       'access_token_url', 'profile_url', 'consumer_key',
                                       'consumer_secret']
        widgets = {
            'name': forms.TextInput(),
            'consumer_key': forms.TextInput(),
            'consumer_secret': forms.TextInput(),
            'provider_type': forms.Select(choices=MANAGER.get_name_tuple()),
            'policies': FilteredSelectMultiple(_('policies'), False)
        }
        labels = {
            'request_token_url': _('Request Token URL'),
            'authorization_url': _('Authorization URL'),
            'access_token_url': _('Access Token URL'),
            'profile_url': _('Profile URL'),
        }


class GitHubOAuthSourceForm(OAuthSourceForm):
    """OAuth Source form with pre-determined URL for GitHub"""

    class Meta(OAuthSourceForm.Meta):

        overrides = {
            'provider_type': 'github',
            'request_token_url': '',
            'authorization_url': 'https://github.com/login/oauth/authorize',
            'access_token_url': 'https://github.com/login/oauth/access_token',
            'profile_url': ' https://api.github.com/user',
        }


class TwitterOAuthSourceForm(OAuthSourceForm):
    """OAuth Source form with pre-determined URL for Twitter"""

    class Meta(OAuthSourceForm.Meta):

        overrides = {
            'provider_type': 'twitter',
            'request_token_url': 'https://api.twitter.com/oauth/request_token',
            'authorization_url': 'https://api.twitter.com/oauth/authenticate',
            'access_token_url': 'https://api.twitter.com/oauth/access_token',
            'profile_url': ' https://api.twitter.com/1.1/account/verify_credentials.json',
        }


class FacebookOAuthSourceForm(OAuthSourceForm):
    """OAuth Source form with pre-determined URL for Facebook"""

    class Meta(OAuthSourceForm.Meta):

        overrides = {
            'provider_type': 'facebook',
            'request_token_url': '',
            'authorization_url': 'https://www.facebook.com/v2.8/dialog/oauth',
            'access_token_url': 'https://graph.facebook.com/v2.8/oauth/access_token',
            'profile_url': ' https://graph.facebook.com/v2.8/me?fields=name,email,short_name',
        }


class DiscordOAuthSourceForm(OAuthSourceForm):
    """OAuth Source form with pre-determined URL for Discord"""

    class Meta(OAuthSourceForm.Meta):

        overrides = {
            'provider_type': 'discord',
            'request_token_url': '',
            'authorization_url': 'https://discordapp.com/api/oauth2/authorize',
            'access_token_url': 'https://discordapp.com/api/oauth2/token',
            'profile_url': ' https://discordapp.com/api/users/@me',
        }


class GoogleOAuthSourceForm(OAuthSourceForm):
    """OAuth Source form with pre-determined URL for Google"""

    class Meta(OAuthSourceForm.Meta):

        overrides = {
            'provider_type': 'google',
            'request_token_url': '',
            'authorization_url': 'https://accounts.google.com/o/oauth2/auth',
            'access_token_url': 'https://accounts.google.com/o/oauth2/token',
            'profile_url': ' https://www.googleapis.com/oauth2/v1/userinfo',
        }


class AzureADOAuthSourceForm(OAuthSourceForm):
    """OAuth Source form with pre-determined URL for AzureAD"""

    class Meta(OAuthSourceForm.Meta):

        overrides = {
            'provider_type': 'azure_ad',
            'request_token_url': '',
            'authorization_url': 'https://login.microsoftonline.com/common/oauth2/authorize',
            'access_token_url': 'https://login.microsoftonline.com/common/oauth2/token',
            'profile_url': ' https://graph.windows.net/myorganization/me?api-version=1.6',
        }
