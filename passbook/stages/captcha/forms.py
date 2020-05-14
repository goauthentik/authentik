"""passbook captcha stage forms"""
from captcha.fields import ReCaptchaField
from django import forms

from passbook.stages.captcha.models import CaptchaStage


class CaptchaForm(forms.Form):
    """passbook captcha stage form"""

    captcha = ReCaptchaField()


class CaptchaStageForm(forms.ModelForm):
    """Form to edit CaptchaStage Instance"""

    class Meta:

        model = CaptchaStage
        fields = ["name", "public_key", "private_key"]
        widgets = {
            "name": forms.TextInput(),
            "public_key": forms.TextInput(),
            "private_key": forms.TextInput(),
        }
