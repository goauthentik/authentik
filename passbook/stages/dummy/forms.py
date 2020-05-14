"""passbook administration forms"""
from django import forms

from passbook.stages.dummy.models import DummyStage


class DummyStageForm(forms.ModelForm):
    """Form to create/edit Dummy Stage"""

    class Meta:

        model = DummyStage
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(),
        }
