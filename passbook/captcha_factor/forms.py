"""passbook captcha factor forms"""
from captcha.fields import ReCaptchaField
from django import forms

from passbook.captcha_factor.models import CaptchaFactor
from passbook.core.forms.factors import GENERAL_FIELDS


class CaptchaForm(forms.Form):
    """passbook captcha factor form"""

    captcha = ReCaptchaField()

class CaptchaFactorForm(forms.ModelForm):
    """Form to edit CaptchaFactor Instance"""

    class Meta:

        model = CaptchaFactor
        fields = GENERAL_FIELDS + ['public_key', 'private_key']
        widgets = {
            'name': forms.TextInput(),
            'order': forms.NumberInput(),
            'public_key': forms.TextInput(),
            'private_key': forms.TextInput(),
        }
