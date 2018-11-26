"""passbook oauth_client forms"""

from django import forms

from passbook.admin.forms.source import SOURCE_FORM_FIELDS
from passbook.oauth_client.models import OAuthSource


class OAuthSourceForm(forms.ModelForm):
    """OAuthSource Form"""

    class Meta:

        model = OAuthSource
        fields = SOURCE_FORM_FIELDS + ['provider_type', 'request_token_url', 'authorization_url',
                                       'access_token_url', 'profile_url', 'consumer_key',
                                       'consumer_secret']
