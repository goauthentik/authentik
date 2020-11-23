"""Prompt forms"""
from email.policy import Policy
from types import MethodType
from typing import Any, Callable, Iterator, List

from django import forms
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import get_anonymous_user

from passbook.core.models import User
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from passbook.policies.engine import PolicyEngine
from passbook.policies.models import PolicyBinding, PolicyBindingModel
from passbook.stages.prompt.models import FieldTypes, Prompt, PromptStage
from passbook.stages.prompt.signals import password_validate


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


class ListPolicyEngine(PolicyEngine):
    """Slightly modified policy engine, which uses a list instead of a PolicyBindingModel"""

    __list: List[Policy]

    def __init__(
        self, policies: List[Policy], user: User, request: HttpRequest = None
    ) -> None:
        super().__init__(PolicyBindingModel(), user, request)
        self.__list = policies
        self.use_cache = False

    def _iter_bindings(self) -> Iterator[PolicyBinding]:
        for policy in self.__list:
            yield PolicyBinding(
                policy=policy,
            )


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
                    MethodType(username_field_cleaner_factory(field), self),
                )
            # Check if we have a password field, add a handler that sends a signal
            # to validate it
            if field.type == FieldTypes.PASSWORD:
                setattr(
                    self,
                    f"clean_{field.field_key}",
                    MethodType(password_single_cleaner_factory(field), self),
                )

        self.field_order = sorted(fields, key=lambda x: x.order)

    def _clean_password_fields(self, *field_names):
        """Check if the value of all password fields match by merging them into a set
        and checking the length"""
        all_passwords = {self.cleaned_data[x] for x in field_names}
        if len(all_passwords) > 1:
            raise forms.ValidationError(_("Passwords don't match."))

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data == {}:
            return {}
        # Check if we have two password fields, and make sure they are the same
        password_fields: QuerySet[Prompt] = self.stage.fields.filter(
            type=FieldTypes.PASSWORD
        )
        if password_fields.exists() and password_fields.count() == 2:
            self._clean_password_fields(*[field.field_key for field in password_fields])

        user = self.plan.context.get(PLAN_CONTEXT_PENDING_USER, get_anonymous_user())
        engine = ListPolicyEngine(self.stage.validation_policies.all(), user)
        engine.request.context = cleaned_data
        engine.build()
        result = engine.result
        if not result.passing:
            raise forms.ValidationError(list(result.messages))
        return cleaned_data


def username_field_cleaner_factory(field: Prompt) -> Callable:
    """Return a `clean_` method for `field`. Clean method checks if username is taken already."""

    def username_field_cleaner(self: PromptForm) -> Any:
        """Check for duplicate usernames"""
        username = self.cleaned_data.get(field.field_key)
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username is already taken.")
        return username

    return username_field_cleaner


def password_single_cleaner_factory(field: Prompt) -> Callable[[PromptForm], Any]:
    """Return a `clean_` method for `field`. Clean method checks if username is taken already."""

    def password_single_clean(self: PromptForm) -> Any:
        """Send password validation signals for e.g. LDAP Source"""
        password = self.cleaned_data[field.field_key]
        password_validate.send(
            sender=self, password=password, plan_context=self.plan.context
        )
        return password

    return password_single_clean
