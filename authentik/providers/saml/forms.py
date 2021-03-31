"""authentik SAML IDP Forms"""

from xml.etree.ElementTree import ParseError  # nosec

from defusedxml.ElementTree import fromstring
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow, FlowDesignation
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider


class SAMLProviderForm(forms.ModelForm):
    """SAML Provider form"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["authorization_flow"].queryset = Flow.objects.filter(
            designation=FlowDesignation.AUTHORIZATION
        )
        self.fields["property_mappings"].queryset = SAMLPropertyMapping.objects.all()
        self.fields["signing_kp"].queryset = CertificateKeyPair.objects.exclude(
            key_data__iexact=""
        )

    class Meta:

        model = SAMLProvider
        fields = [
            "name",
            "authorization_flow",
            "acs_url",
            "issuer",
            "sp_binding",
            "audience",
            "signing_kp",
            "verification_kp",
            "property_mappings",
            "name_id_mapping",
            "assertion_valid_not_before",
            "assertion_valid_not_on_or_after",
            "session_valid_not_on_or_after",
            "digest_algorithm",
            "signature_algorithm",
        ]
        widgets = {
            "name": forms.TextInput(),
            "audience": forms.TextInput(),
            "issuer": forms.TextInput(),
            "assertion_valid_not_before": forms.TextInput(),
            "assertion_valid_not_on_or_after": forms.TextInput(),
            "session_valid_not_on_or_after": forms.TextInput(),
        }


class SAMLProviderImportForm(forms.Form):
    """Create a SAML Provider from SP Metadata."""

    provider_name = forms.CharField()
    authorization_flow = forms.ModelChoiceField(
        queryset=Flow.objects.filter(designation=FlowDesignation.AUTHORIZATION)
    )
    metadata = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["xml"])]
    )

    def clean_metadata(self):
        """Check if the flow is valid XML"""
        metadata = self.cleaned_data["metadata"].read()
        try:
            fromstring(metadata)
        except ParseError:
            raise ValidationError(_("Invalid XML Syntax"))
        self.cleaned_data["metadata"].seek(0)
        return self.cleaned_data["metadata"]
