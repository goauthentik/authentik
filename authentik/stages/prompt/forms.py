"""Prompt forms"""
from django import forms

from authentik.stages.prompt.models import PromptStage


class PromptStageForm(forms.ModelForm):
    """Form to create/edit Prompt Stage instances"""

    class Meta:

        model = PromptStage
        fields = ["name", "fields", "validation_policies"]
        widgets = {
            "name": forms.TextInput(),
        }
