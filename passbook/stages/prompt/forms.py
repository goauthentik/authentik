"""Prompt forms"""
from django import forms

from passbook.stages.prompt.models import Prompt, PromptStage


class PromptStageForm(forms.ModelForm):
    """Form to create/edit Prompt Stage instances"""

    class Meta:

        model = PromptStage
        fields = ["name", "fields"]
        widgets = {
            "name": forms.TextInput(),
        }


class PromptForm(forms.Form):
    """Dynamically created form based on PromptStage"""

    stage: PromptStage

    def __init__(self, stage: PromptStage, *args, **kwargs):
        self.stage = stage
        super().__init__(*args, **kwargs)
        for field in self.stage.fields.all():
            field: Prompt
            self.fields[field.field_key] = field.field
