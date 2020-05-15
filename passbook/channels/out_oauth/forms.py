"""passbook OAuth2 Outlet Forms"""

from django import forms

from passbook.channels.out_oauth.models import OAuth2Outlet


class OAuth2OutletForm(forms.ModelForm):
    """OAuth2 Outlet form"""

    class Meta:

        model = OAuth2Outlet
        fields = [
            "name",
            "redirect_uris",
            "client_type",
            "authorization_grant_type",
            "client_id",
            "client_secret",
        ]
