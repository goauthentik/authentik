from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from passbook.stages.otp_validate.models import OTPValidateStage

OTP_CODE_VALIDATOR = RegexValidator(
    r"^[0-9a-z]{6,8}$", _("Only alpha-numeric characters are allowed.")
)


class ValidationForm(forms.Form):

    code = forms.CharField(
        label=_("Code"),
        validators=[OTP_CODE_VALIDATOR],
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "placeholder": "Code",
                "autofocus": "autofocus",
            }
        ),
    )

    def clean_code(self):
        pass


class OTPValidateStageForm(forms.ModelForm):
    class Meta:

        model = OTPValidateStage
        fields = ["name"]

        widgets = {
            "name": forms.TextInput(),
        }
