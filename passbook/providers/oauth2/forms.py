"""passbook OAuth2 Provider Forms"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from passbook.admin.fields import CodeMirrorWidget
from passbook.core.expression import PropertyMappingEvaluator
from passbook.crypto.models import CertificateKeyPair
from passbook.flows.models import Flow, FlowDesignation
from passbook.providers.oauth2.generators import (
    generate_client_id,
    generate_client_secret,
)
from passbook.providers.oauth2.models import OAuth2Provider, ScopeMapping


class OAuth2ProviderForm(forms.ModelForm):
    """OAuth2 Provider form"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["authorization_flow"].queryset = Flow.objects.filter(
            designation=FlowDesignation.AUTHORIZATION
        )
        self.fields["client_id"].initial = generate_client_id()
        self.fields["client_secret"].initial = generate_client_secret()
        self.fields["rsa_key"].queryset = CertificateKeyPair.objects.exclude(
            key_data__exact=""
        )
        self.fields["property_mappings"].queryset = ScopeMapping.objects.all()

    def clean_jwt_alg(self):
        """Ensure that when RS256 is selected, a certificate-key-pair is selected"""
        if "rsa_key" not in self.cleaned_data:
            raise ValidationError(
                _("RS256 requires a Certificate-Key-Pair to be selected.")
            )
        return self.cleaned_data["jwt_alg"]

    class Meta:
        model = OAuth2Provider
        fields = [
            "name",
            "authorization_flow",
            "client_type",
            "client_id",
            "client_secret",
            "response_type",
            "token_validity",
            "jwt_alg",
            "rsa_key",
            "redirect_uris",
            "sub_mode",
            "property_mappings",
        ]
        widgets = {
            "name": forms.TextInput(),
            "token_validity": forms.TextInput(),
        }
        labels = {"property_mappings": _("Scopes")}
        help_texts = {
            "property_mappings": _(
                (
                    "Select which scopes <b>can</b> be used by the client. "
                    "The client stil has to specify the scope to access the data."
                )
            )
        }


class ScopeMappingForm(forms.ModelForm):
    """Form to edit ScopeMappings"""

    def clean_expression(self):
        """Test Syntax"""
        expression = self.cleaned_data.get("expression")
        evaluator = PropertyMappingEvaluator()
        evaluator.validate(expression)
        return expression

    class Meta:

        model = ScopeMapping
        fields = ["name", "scope_name", "description", "expression"]
        widgets = {
            "name": forms.TextInput(),
            "scope_name": forms.TextInput(),
            "description": forms.TextInput(),
            "expression": CodeMirrorWidget(mode="python"),
        }
