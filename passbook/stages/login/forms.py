"""passbook flows login forms"""
from django import forms

from passbook.stages.login.models import LoginStage


class LoginStageForm(forms.ModelForm):
    """Form to create/edit LoginStage instances"""

    class Meta:

        model = LoginStage
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(),
        }
