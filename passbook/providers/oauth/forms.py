"""passbook OAuth2 Provider Forms"""

from django import forms

from passbook.providers.oauth.models import OAuth2Provider


class OAuth2ProviderForm(forms.ModelForm):
    """OAuth2 Provider form"""

    class Meta:

        model = OAuth2Provider
        fields = [
            "name",
            "authorization_flow",
            "redirect_uris",
            "client_type",
            "authorization_grant_type",
            "client_id",
            "client_secret",
        ]
