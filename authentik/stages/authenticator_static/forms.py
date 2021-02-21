"""Static Authenticator forms"""
from django import forms

from authentik.stages.authenticator_static.models import AuthenticatorStaticStage


class AuthenticatorStaticStageForm(forms.ModelForm):
    """Static Authenticator Stage setup form"""

    class Meta:

        model = AuthenticatorStaticStage
        fields = ["name", "configure_flow", "token_count"]

        widgets = {
            "name": forms.TextInput(),
        }
