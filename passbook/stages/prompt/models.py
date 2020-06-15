"""prompt models"""
from uuid import uuid4

from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Stage
from passbook.policies.models import PolicyBindingModel


class FieldTypes(models.TextChoices):
    """Field types an Prompt can be"""

    # Simple text field
    TEXT = "text"
    # Same as text, but has autocomplete for password managers
    USERNAME = "username"
    EMAIL = "e-mail"
    PASSWORD = "password"  # noqa # nosec
    NUMBER = "number"
    CHECKBOX = "checkbox"
    DATE = "data"
    DATE_TIME = "data-time"

    SEPARATOR = "separator"
    HIDDEN = "hidden"
    STATIC = "static"


class Prompt(models.Model):
    """Single Prompt, part of a prompt stage."""

    prompt_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    field_key = models.SlugField(
        help_text=_("Name of the form field, also used to store the value")
    )
    label = models.TextField()
    type = models.CharField(max_length=100, choices=FieldTypes.choices)
    required = models.BooleanField(default=True)
    placeholder = models.TextField()

    order = models.IntegerField(default=0)

    @property
    def field(self):
        """Return instantiated form input field"""
        attrs = {"placeholder": _(self.placeholder)}
        field_class = forms.CharField
        widget = forms.TextInput(attrs=attrs)
        kwargs = {
            "label": _(self.label),
            "required": self.required,
        }
        if self.type == FieldTypes.EMAIL:
            field_class = forms.EmailField
        if self.type == FieldTypes.USERNAME:
            attrs["autocomplete"] = "username"
        if self.type == FieldTypes.PASSWORD:
            widget = forms.PasswordInput(attrs=attrs)
            attrs["autocomplete"] = "new-password"
        if self.type == FieldTypes.NUMBER:
            field_class = forms.IntegerField
            widget = forms.NumberInput(attrs=attrs)
        if self.type == FieldTypes.HIDDEN:
            widget = forms.HiddenInput(attrs=attrs)
            kwargs["required"] = False
            kwargs["initial"] = self.placeholder
        if self.type == FieldTypes.CHECKBOX:
            field_class = forms.CheckboxInput
            kwargs["required"] = False
        if self.type == FieldTypes.DATE:
            field_class = forms.DateInput
        if self.type == FieldTypes.DATE_TIME:
            field_class = forms.DateTimeInput

        # TODO: Implement static
        # TODO: Implement separator
        kwargs["widget"] = widget
        return field_class(**kwargs)

    def save(self, *args, **kwargs):
        if self.type not in FieldTypes:
            raise ValueError
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Prompt '{self.field_key}' type={self.type}"

    class Meta:

        verbose_name = _("Prompt")
        verbose_name_plural = _("Prompts")


class PromptStage(PolicyBindingModel, Stage):
    """Prompt Stage, pointing to multiple prompts"""

    fields = models.ManyToManyField(Prompt)

    type = "passbook.stages.prompt.stage.PromptStageView"
    form = "passbook.stages.prompt.forms.PromptStageForm"

    def __str__(self):
        return f"Prompt Stage {self.name}"

    class Meta:

        verbose_name = _("Prompt Stage")
        verbose_name_plural = _("Prompt Stages")
