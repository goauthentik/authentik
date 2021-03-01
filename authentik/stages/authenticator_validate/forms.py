"""OTP Validate stage forms"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django_otp import match_token

from authentik.core.models import User
from authentik.flows.models import NotConfiguredAction
from authentik.stages.authenticator_validate.models import (
    AuthenticatorValidateStage,
    DeviceClasses,
)


class ValidationForm(forms.Form):
    """OTP Validate stage forms"""

    user: User

    code = forms.CharField(
        label=_("Please enter the token from your device."),
        widget=forms.TextInput(
            attrs={
                "autocomplete": "one-time-code",
                "placeholder": "123456",
                "autofocus": "autofocus",
            }
        ),
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_code(self):
        """Validate code against all confirmed devices"""
        code = self.cleaned_data.get("code")
        device = match_token(self.user, code)
        if not device:
            raise forms.ValidationError(_("Invalid Token"))
        return code


class AuthenticatorValidateStageForm(forms.ModelForm):
    """OTP Validate stage forms"""

    def clean_not_configured_action(self):
        """Ensure that a configuration stage is set when not_configured_action is configure"""
        not_configured_action = self.cleaned_data.get("not_configured_action")
        configuration_stage = self.cleaned_data.get("configuration_stage")
        if (
            not_configured_action == NotConfiguredAction.CONFIGURE
            and configuration_stage is None
        ):
            raise forms.ValidationError(
                (
                    'When "Not configured action" is set to "Configure", '
                    "you must set a configuration stage."
                )
            )
        return not_configured_action

    class Meta:

        model = AuthenticatorValidateStage
        fields = [
            "name",
            "not_configured_action",
            "device_classes",
            "configuration_stage",
        ]

        widgets = {
            "name": forms.TextInput(),
            "device_classes": forms.SelectMultiple(choices=DeviceClasses.choices),
        }
