"""Webauthn stage forms"""
from django import forms

from authentik.stages.authenticator_webauthn.models import (
    AuthenticateWebAuthnStage,
    WebAuthnDevice,
)


class AuthenticateWebAuthnStageForm(forms.ModelForm):
    """OTP Time-based Stage setup form"""

    class Meta:

        model = AuthenticateWebAuthnStage
        fields = ["name"]

        widgets = {
            "name": forms.TextInput(),
        }


class DeviceEditForm(forms.ModelForm):
    """Form to edit webauthn device"""

    class Meta:

        model = WebAuthnDevice
        fields = ["name"]

        widgets = {
            "name": forms.TextInput(),
        }
