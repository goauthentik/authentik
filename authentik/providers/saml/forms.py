"""authentik SAML IDP Forms"""

from django import forms
from django.utils.html import mark_safe
from django.utils.translation import gettext as _

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
            "audience",
            "issuer",
            "sp_binding",
            "assertion_valid_not_before",
            "assertion_valid_not_on_or_after",
            "session_valid_not_on_or_after",
            "digest_algorithm",
            "signature_algorithm",
            "signing_kp",
            "verification_kp",
            "property_mappings",
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
                    '<a href="https://www.rfc-editor.org/rfc/rfc2798.html#section-2">Reference</a>'
                )
            ),
        }
