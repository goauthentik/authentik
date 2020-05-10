"""passbook flows create forms"""
from django import forms

from passbook.stages.user_create.models import UserCreateStage


class UserCreateStageForm(forms.ModelForm):
    """Form to create/edit UserCreateStage instances"""

    class Meta:

        model = UserCreateStage
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(),
        }
