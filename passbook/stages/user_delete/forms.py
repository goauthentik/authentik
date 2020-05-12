"""passbook flows delete forms"""
from django import forms

from passbook.stages.user_delete.models import UserDeleteStage


class UserDeleteStageForm(forms.ModelForm):
    """Form to delete/edit UserDeleteStage instances"""

    class Meta:

        model = UserDeleteStage
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(),
        }


class UserDeleteForm(forms.Form):
    """Confirmation form to ensure user knows they are deleting their profile"""
