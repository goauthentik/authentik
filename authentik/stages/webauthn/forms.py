from django import forms

from authentik.stages.webauthn.models import WebAuthnStage


class WebAuthnStageForm(forms.ModelForm):
    """OTP Time-based Stage setup form"""

    class Meta:

        model = WebAuthnStage
        fields = ["name"]

        widgets = {
            "name": forms.TextInput(),
        }
