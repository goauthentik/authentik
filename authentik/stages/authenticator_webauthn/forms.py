from django import forms

from authentik.stages.authenticator_webauthn.models import AuthenticateWebAuthnStage


class AuthenticateWebAuthnStageForm(forms.ModelForm):
    """OTP Time-based Stage setup form"""

    class Meta:

        model = AuthenticateWebAuthnStage
        fields = ["name"]

        widgets = {
            "name": forms.TextInput(),
        }
