"""authentik SAML IDP Forms"""

from xml.etree.ElementTree import ParseError  # nosec

from defusedxml.ElementTree import fromstring
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _

from authentik.admin.fields import CodeMirrorWidget
from authentik.core.expression import PropertyMappingEvaluator
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


class SAMLPropertyMappingForm(forms.ModelForm):
    """SAML Property Mapping form"""

    template_name = "providers/saml/property_mapping_form.html"

    def clean_expression(self):
        """Test Syntax"""
        expression = self.cleaned_data.get("expression")
        evaluator = PropertyMappingEvaluator()
        evaluator.validate(expression)
        return expression

    class Meta:

        model = SAMLPropertyMapping
        fields = ["name", "saml_name", "friendly_name", "expression"]
        widgets = {
            "name": forms.TextInput(),
            "saml_name": forms.TextInput(),
            "friendly_name": forms.TextInput(),
            "expression": CodeMirrorWidget(mode="python"),
        }
        help_texts = {
            "saml_name": mark_safe(
                _(
                    "URN OID used by SAML. This is optional. "
                    '<a href="https://www.rfc-editor.org/rfc/rfc2798.html#section-2">Reference</a>.'
                    " If this property mapping is used for NameID Property, "
                    "this field is discarded."
                )
            ),
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
