"""passbook OAuth2 Provider Forms"""

from django import forms
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Flow, FlowDesignation
from passbook.providers.oauth.models import OAuth2Provider


class OAuth2ProviderForm(forms.ModelForm):
    """OAuth2 Provider form"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["authorization_flow"].queryset = Flow.objects.filter(
            designation=FlowDesignation.AUTHORIZATION
        )

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
        labels = {
            "client_id": _("Client ID"),
            "redirect_uris": _("Redirect URIs"),
        }
