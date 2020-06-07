"""passbook OIDC IDP Forms"""

from django import forms
from oauth2_provider.generators import generate_client_id, generate_client_secret
from oidc_provider.models import Client

from passbook.flows.models import Flow, FlowDesignation
from passbook.providers.oidc.models import OpenIDProvider


class OIDCProviderForm(forms.ModelForm):
    """OpenID Client form"""

    authorization_flow = forms.ModelChoiceField(
        queryset=Flow.objects.filter(designation=FlowDesignation.AUTHORIZATION)
    )

    def __init__(self, *args, **kwargs):
        # Correctly load data from 1:1 rel
        if "instance" in kwargs and kwargs["instance"]:
            kwargs["instance"] = kwargs["instance"].oidc_client
        super().__init__(*args, **kwargs)
        self.fields["client_id"].initial = generate_client_id()
        self.fields["client_secret"].initial = generate_client_secret()
        try:
            self.fields[
                "authorization_flow"
            ].initial = self.instance.openidprovider.authorization_flow
        # pylint: disable=no-member
        except Client.openidprovider.RelatedObjectDoesNotExist:
            pass

    def save(self, *args, **kwargs):
        self.instance.reuse_consent = False  # This is managed by passbook
        self.instance.require_consent = False  # This is managed by passbook
        response = super().save(*args, **kwargs)
        # Check if openidprovider class instance exists
        if not OpenIDProvider.objects.filter(oidc_client=self.instance).exists():
            OpenIDProvider.objects.create(
                oidc_client=self.instance,
                authorization_flow=self.cleaned_data.get("authorization_flow"),
            )
        self.instance.openidprovider.authorization_flow = self.cleaned_data.get(
            "authorization_flow"
        )
        self.instance.openidprovider.save()
        return response

    class Meta:
        model = Client
        fields = [
            "name",
            "authorization_flow",
            "client_type",
            "client_id",
            "client_secret",
            "response_types",
            "jwt_alg",
            "_redirect_uris",
            "_scope",
        ]
        labels = {"client_secret": "Client Secret"}
