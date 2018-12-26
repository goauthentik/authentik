"""passbook SAML IDP Forms"""

from django import forms

from passbook.saml_idp.models import SAMLProvider, get_provider_choices
from passbook.saml_idp.utils import CertificateBuilder


class SAMLProviderForm(forms.ModelForm):
    """SAML Provider form"""

    processor_path = forms.ChoiceField(choices=get_provider_choices(), label='Processor')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        builder = CertificateBuilder()
        builder.build()
        self.fields['signing_cert'].initial = builder.certificate
        self.fields['signing_key'].initial = builder.private_key

    class Meta:

        model = SAMLProvider
        fields = ['name', 'acs_url', 'processor_path', 'issuer',
                  'assertion_valid_for', 'signing', 'signing_cert', 'signing_key', ]
        labels = {
            'acs_url': 'ACS URL',
            'signing_cert': 'Singing Certificate',
        }
        widgets = {
            'name': forms.TextInput(),
            'issuer': forms.TextInput(),
        }
