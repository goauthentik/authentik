"""passbook flows write forms"""
from django import forms

from passbook.stages.user_write.models import UserWriteStage


class UserWriteStageForm(forms.ModelForm):
    """Form to write/edit UserWriteStage instances"""

    class Meta:

        model = UserWriteStage
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(),
        }
