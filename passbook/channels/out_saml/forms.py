"""passbook SAML IDP Forms"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext as _

from passbook.channels.out_saml.models import (
    SAMLOutlet,
    SAMLPropertyMapping,
    get_provider_choices,
)


class SAMLOutletForm(forms.ModelForm):
    """SAML Outlet form"""

    processor_path = forms.ChoiceField(
        choices=get_provider_choices(), label="Processor"
    )

    class Meta:

        model = SAMLOutlet
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
            "require_signing",
            "signature_algorithm",
            "signing_kp",
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
