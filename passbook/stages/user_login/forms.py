"""passbook flows login forms"""
from django import forms

from passbook.stages.user_login.models import UserLoginStage


class UserLoginStageForm(forms.ModelForm):
    """Form to create/edit UserLoginStage instances"""

    class Meta:

        model = UserLoginStage
        fields = ["name", "session_duration"]
        widgets = {
            "name": forms.TextInput(),
        }
