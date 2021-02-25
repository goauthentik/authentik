"""authentik captcha stage forms"""
from django import forms

from authentik.stages.captcha.models import CaptchaStage


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
