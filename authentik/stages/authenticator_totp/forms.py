"""OTP Time forms"""
from django import forms

from authentik.stages.authenticator_totp.models import AuthenticatorTOTPStage


class AuthenticatorTOTPStageForm(forms.ModelForm):
    """OTP Time-based Stage setup form"""

    class Meta:

        model = AuthenticatorTOTPStage
        fields = ["name", "configure_flow", "digits"]

        widgets = {
            "name": forms.TextInput(),
        }
