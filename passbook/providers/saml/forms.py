"""passbook SAML IDP Forms"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext as _

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
            "digest_algorithm",
            "signature_algorithm",
            "signing",
            "signing_cert",
            "signing_key",
        ]
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

    template_name = "saml/idp/property_mapping_form.html"

    class Meta:

        model = SAMLPropertyMapping
        fields = ["name", "saml_name", "friendly_name", "expression"]
        widgets = {
            "name": forms.TextInput(),
            "saml_name": forms.TextInput(),
            "friendly_name": forms.TextInput(),
        }
