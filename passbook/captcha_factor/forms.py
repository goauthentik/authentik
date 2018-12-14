"""passbook captcha factor forms"""
from captcha.fields import ReCaptchaField
from django import forms


class CaptchaForm(forms.Form):
    """passbook captcha factor form"""

    captcha = ReCaptchaField()
