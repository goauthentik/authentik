"""authentik consent stage forms"""
from django import forms

from authentik.stages.consent.models import ConsentStage


class ConsentForm(forms.Form):
    """authentik consent stage form"""


class ConsentStageForm(forms.ModelForm):
    """Form to edit ConsentStage Instance"""

    class Meta:

        model = ConsentStage
        fields = ["name", "mode", "consent_expire_in"]
        widgets = {
            "name": forms.TextInput(),
            "consent_expire_in": forms.TextInput(),
        }
