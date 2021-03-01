"""authentik flows deny forms"""
from django import forms

from authentik.stages.deny.models import DenyStage


class DenyStageForm(forms.ModelForm):
    """Form to create/edit DenyStage instances"""

    class Meta:

        model = DenyStage
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(),
        }
