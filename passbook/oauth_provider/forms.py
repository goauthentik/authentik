"""passbook OAuth2 Provider Forms"""

from django import forms

from passbook.oauth_provider.models import OAuth2Provider


class OAuth2ProviderForm(forms.ModelForm):
    """OAuth2 Provider form"""

    class Meta:

        model = OAuth2Provider
        fields = ['name', 'redirect_uris', 'client_type',
                  'authorization_grant_type', 'client_id', 'client_secret', ]
