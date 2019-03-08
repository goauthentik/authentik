"""passbook SAML IDP Forms"""

from django import forms

from passbook.lib.fields import DynamicArrayField
from passbook.saml_idp.models import (SAMLPropertyMapping, SAMLProvider,
                                      get_provider_choices)
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
        fields = ['name', 'property_mappings', 'acs_url', 'processor_path', 'issuer',
                  'assertion_valid_for', 'signing', 'signing_cert', 'signing_key', ]
        labels = {
            'acs_url': 'ACS URL',
            'signing_cert': 'Singing Certificate',
        }
        widgets = {
            'name': forms.TextInput(),
            'issuer': forms.TextInput(),
        }


class SAMLPropertyMappingForm(forms.ModelForm):
    """SAML Property Mapping form"""

    class Meta:

        model = SAMLPropertyMapping
        fields = ['name', 'saml_name', 'friendly_name', 'values']
        widgets = {
            'name': forms.TextInput(),
            'saml_name': forms.TextInput(),
            'friendly_name': forms.TextInput(),
        }
        field_classes = {
            'values': DynamicArrayField
        }
