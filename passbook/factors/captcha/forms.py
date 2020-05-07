"""passbook captcha factor forms"""
from captcha.fields import ReCaptchaField
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from passbook.factors.captcha.models import CaptchaFactor
from passbook.flows.forms import GENERAL_FIELDS


class CaptchaForm(forms.Form):
    """passbook captcha factor form"""

    captcha = ReCaptchaField()


class CaptchaFactorForm(forms.ModelForm):
    """Form to edit CaptchaFactor Instance"""

    class Meta:

        model = CaptchaFactor
        fields = GENERAL_FIELDS + ["public_key", "private_key"]
        widgets = {
            "name": forms.TextInput(),
            "order": forms.NumberInput(),
            "policies": FilteredSelectMultiple(_("policies"), False),
            "public_key": forms.TextInput(),
            "private_key": forms.TextInput(),
        }
        help_texts = {
            "policies": _(
                "Policies which determine if this factor applies to the current user."
            )
        }
