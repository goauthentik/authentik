"""Prompt forms"""
from django import forms
from guardian.shortcuts import get_anonymous_user

from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from passbook.policies.engine import PolicyEngine
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
    plan: FlowPlan

    def __init__(self, stage: PromptStage, plan: FlowPlan, *args, **kwargs):
        self.stage = stage
        self.plan = plan
        super().__init__(*args, **kwargs)
        for field in self.stage.fields.all():
            field: Prompt
            self.fields[field.field_key] = field.field

    def clean(self):
        cleaned_data = super().clean()
        user = self.plan.context.get(PLAN_CONTEXT_PENDING_USER, get_anonymous_user())
        engine = PolicyEngine(self.stage.policies.all(), user)
        engine.request.context = cleaned_data
        engine.build()
        passing, messages = engine.result
        if not passing:
            raise forms.ValidationError(messages)
