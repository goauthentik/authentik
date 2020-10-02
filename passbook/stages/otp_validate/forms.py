"""OTP Validate stage forms"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django_otp import match_token

from passbook.core.models import User
from passbook.stages.otp_validate.models import OTPValidateStage


class ValidationForm(forms.Form):
    """OTP Validate stage forms"""

    user: User

    code = forms.CharField(
        label=_("Please enter the token from your device."),
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
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


class OTPValidateStageForm(forms.ModelForm):
    """OTP Validate stage forms"""

    class Meta:

        model = OTPValidateStage
        fields = ["name"]

        widgets = {
            "name": forms.TextInput(),
        }
