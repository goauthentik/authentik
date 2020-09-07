"""Prompt forms"""
from typing import Callable

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import get_anonymous_user

from passbook.core.models import User
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from passbook.policies.engine import PolicyEngine
from passbook.stages.prompt.models import FieldTypes, Prompt, PromptStage


class PromptStageForm(forms.ModelForm):
    """Form to create/edit Prompt Stage instances"""

    class Meta:

        model = PromptStage
        fields = ["name", "fields"]
        widgets = {
            "name": forms.TextInput(),
            "fields": FilteredSelectMultiple(_("prompts"), False),
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


class PromptForm(forms.Form):
    """Dynamically created form based on PromptStage"""

    stage: PromptStage
    plan: FlowPlan

    def __init__(self, stage: PromptStage, plan: FlowPlan, *args, **kwargs):
        self.stage = stage
        self.plan = plan
        super().__init__(*args, **kwargs)
        # list() is called so we only load the fields once
        fields = list(self.stage.fields.all())
        for field in fields:
            field: Prompt
            self.fields[field.field_key] = field.field
            # Special handling for fields with username type
            # these check for existing users with the same username
            if field.type == FieldTypes.USERNAME:
                setattr(
                    self,
                    f"clean_{field.field_key}",
                    username_field_cleaner_generator(field),
                )
        self.field_order = sorted(fields, key=lambda x: x.order)

    def clean(self):
        cleaned_data = super().clean()
        user = self.plan.context.get(PLAN_CONTEXT_PENDING_USER, get_anonymous_user())
        engine = PolicyEngine(self.stage, user)
        engine.request.context = cleaned_data
        engine.build()
        result = engine.result
        if not result.passing:
            raise forms.ValidationError(list(result.messages))


def username_field_cleaner_generator(field: Prompt) -> Callable:
    """Return a `clean_` method for `field`. Clean method checks if username is taken already."""

    def username_field_cleaner(self: PromptForm):
        """Check for duplicate usernames"""
        username = self.cleaned_data.get(field.field_key)
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username is already taken.")

    return username_field_cleaner
