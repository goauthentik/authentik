"""passbook SAML SP Forms"""

from django import forms

from passbook.admin.forms.source import SOURCE_FORM_FIELDS
from passbook.flows.models import Flow, FlowDesignation
from passbook.sources.saml.models import SAMLSource


class SAMLSourceForm(forms.ModelForm):
    """SAML Provider form"""

    authentication_flow = forms.ModelChoiceField(
        queryset=Flow.objects.filter(designation=FlowDesignation.AUTHENTICATION)
    )
    enrollment_flow = forms.ModelChoiceField(
        queryset=Flow.objects.filter(designation=FlowDesignation.ENROLLMENT)
    )

    class Meta:

        model = SAMLSource
        fields = SOURCE_FORM_FIELDS + [
            "issuer",
            "sso_url",
            "name_id_policy",
            "binding_type",
            "slo_url",
            "temporary_user_delete_after",
            "signing_kp",
        ]
        widgets = {
            "name": forms.TextInput(),
            "issuer": forms.TextInput(),
            "sso_url": forms.TextInput(),
            "slo_url": forms.TextInput(),
            "temporary_user_delete_after": forms.TextInput(),
        }
