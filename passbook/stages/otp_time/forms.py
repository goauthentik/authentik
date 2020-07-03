"""OTP Time forms"""
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_otp.models import Device

from passbook.stages.otp_time.models import OTPTimeStage
from passbook.stages.otp_validate.forms import OTP_CODE_VALIDATOR


class PictureWidget(forms.widgets.Widget):
    """Widget to render value as img-tag"""

    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe(f"<br>{value}")  # nosec


class SetupForm(forms.Form):
    """Form to setup Time-based OTP"""

    device: Device = None

    qr_code = forms.CharField(
        widget=PictureWidget,
        disabled=True,
        required=False,
        label=_("Scan this Code with your OTP App."),
    )
    code = forms.CharField(
        label=_("Please enter the Token on your device."),
        validators=[OTP_CODE_VALIDATOR],
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "placeholder": "Code",
                "autofocus": "autofocus",
            }
        ),
    )

    def __init__(self, device, qr_code, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device = device
        self.fields["qr_code"].initial = qr_code

    def clean_code(self):
        """Check code with new otp device"""
        if self.device is not None:
            if not self.device.verify_token(self.cleaned_data.get("code")):
                raise forms.ValidationError(_("OTP Code does not match"))
        return self.cleaned_data.get("code")


class OTPTimeStageForm(forms.ModelForm):
    """OTP Time-based Stage setup form"""

    class Meta:

        model = OTPTimeStage
        fields = ["name", "digits"]

        widgets = {
            "name": forms.TextInput(),
        }
