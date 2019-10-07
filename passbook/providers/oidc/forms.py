"""passbook OIDC IDP Forms"""

from django import forms
from oauth2_provider.generators import (generate_client_id,
                                        generate_client_secret)
from oidc_provider.models import Client

from passbook.providers.oidc.models import OpenIDProvider


class OIDCProviderForm(forms.ModelForm):
    """OpenID Client form"""

    def __init__(self, *args, **kwargs):
        # Correctly load data from 1:1 rel
        if 'instance' in kwargs and kwargs['instance']:
            kwargs['instance'] = kwargs['instance'].oidc_client
        super().__init__(*args, **kwargs)
        self.fields['client_id'].initial = generate_client_id()
        self.fields['client_secret'].initial = generate_client_secret()

    def save(self, *args, **kwargs):
        response = super().save(*args, **kwargs)
        # Check if openidprovider class instance exists
        if not OpenIDProvider.objects.filter(oidc_client=self.instance).exists():
            OpenIDProvider.objects.create(oidc_client=self.instance)
        return response

    class Meta:
        model = Client
        fields = [
            'name', 'client_type', 'client_id', 'client_secret', 'response_types',
            'jwt_alg', 'reuse_consent', 'require_consent', '_redirect_uris', '_scope'
        ]
        # exclude = ['owner', 'website_url', 'terms_url', 'contact_email', 'logo', ]
        labels = {
            'client_secret': "Client Secret"
        }
