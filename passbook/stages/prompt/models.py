"""prompt models"""
from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Stage
from uuid import uuid4
from passbook.policies.models import PolicyBindingModel


class FieldTypes(models.TextChoices):
    """Field types an Prompt can be"""

    TEXT = "text"
    EMAIL = "e-mail"
    PASSWORD = "password"  # noqa # nosec
    NUMBER = "number"
    HIDDEN = "hidden"


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

    @property
    def field(self):
        """Return instantiated form input field"""
        attrs = {"placeholder": _(self.placeholder)}
        if self.type == FieldTypes.TEXT:
            return forms.CharField(
                label=_(self.label),
                widget=forms.TextInput(attrs=attrs),
                required=self.required,
            )
        if self.type == FieldTypes.EMAIL:
            return forms.EmailField(
                label=_(self.label),
                widget=forms.TextInput(attrs=attrs),
                required=self.required,
            )
        if self.type == FieldTypes.PASSWORD:
            return forms.CharField(
                label=_(self.label),
                widget=forms.PasswordInput(attrs=attrs),
                required=self.required,
            )
        if self.type == FieldTypes.NUMBER:
            return forms.IntegerField(
                label=_(self.label),
                widget=forms.NumberInput(attrs=attrs),
                required=self.required,
            )
        if self.type == FieldTypes.HIDDEN:
            return forms.CharField(
                widget=forms.HiddenInput(attrs=attrs),
                required=False,
                initial=self.placeholder,
            )
        raise ValueError("field_type is not valid, not one of FieldTypes.")

    def save(self, *args, **kwargs):
        if self.type not in FieldTypes:
            raise ValueError
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Prompt '{self.field_key}' type={self.type}'"

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
