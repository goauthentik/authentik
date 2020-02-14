"""passbook SAML IDP Forms"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext as _

from passbook.lib.fields import DynamicArrayField
from passbook.providers.saml.models import (
    SAMLPropertyMapping,
    SAMLProvider,
    get_provider_choices,
)
from passbook.providers.saml.utils.cert import CertificateBuilder


class SAMLProviderForm(forms.ModelForm):
    """SAML Provider form"""

    processor_path = forms.ChoiceField(
        choices=get_provider_choices(), label="Processor"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        builder = CertificateBuilder()
        builder.build()
        self.fields["signing_cert"].initial = builder.certificate
        self.fields["signing_key"].initial = builder.private_key

    class Meta:

        model = SAMLProvider
        fields = [
            "name",
            "processor_path",
            "acs_url",
            "audience",
            "issuer",
            "assertion_valid_not_before",
            "assertion_valid_not_on_or_after",
            "session_valid_not_on_or_after",
            "property_mappings",
            "signing",
            "signing_cert",
            "signing_key",
        ]
        labels = {
            "acs_url": "ACS URL",
            "signing_cert": "Singing Certificate",
        }
        widgets = {
            "name": forms.TextInput(),
            "audience": forms.TextInput(),
            "issuer": forms.TextInput(),
            "assertion_valid_not_before": forms.TextInput(),
            "assertion_valid_not_on_or_after": forms.TextInput(),
            "session_valid_not_on_or_after": forms.TextInput(),
            "property_mappings": FilteredSelectMultiple(_("Property Mappings"), False),
        }


class SAMLPropertyMappingForm(forms.ModelForm):
    """SAML Property Mapping form"""

    class Meta:

        model = SAMLPropertyMapping
        fields = ["name", "saml_name", "friendly_name", "values"]
        widgets = {
            "name": forms.TextInput(),
            "saml_name": forms.TextInput(),
            "friendly_name": forms.TextInput(),
        }
        field_classes = {"values": DynamicArrayField}
        help_texts = {
            "values": 'String substitution uses a syntax like "{variable} test}".'
        }
