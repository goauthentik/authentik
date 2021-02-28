"""Prompt forms"""
from django import forms

from authentik.stages.prompt.models import Prompt, PromptStage


class PromptStageForm(forms.ModelForm):
    """Form to create/edit Prompt Stage instances"""

    class Meta:

        model = PromptStage
        fields = ["name", "fields", "validation_policies"]
        widgets = {
            "name": forms.TextInput(),
        }


class PromptAdminForm(forms.ModelForm):
    """Form to edit Prompt instances for admins"""

    class Meta:

        model = Prompt
        fields = [
            "field_key",
            "label",
            "type",
            "required",
            "placeholder",
            "order",
        ]
        widgets = {
            "label": forms.TextInput(),
            "placeholder": forms.TextInput(),
        }
