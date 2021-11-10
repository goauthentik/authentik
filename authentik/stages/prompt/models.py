"""prompt models"""
from typing import Any, Optional, Type
from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.fields import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    EmailField,
    HiddenField,
    IntegerField,
    ReadOnlyField,
)
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage
from authentik.lib.models import SerializerModel
from authentik.policies.models import Policy


class FieldTypes(models.TextChoices):
    """Field types an Prompt can be"""

    # Simple text field
    TEXT = "text", _("Text: Simple Text input")
    # Simple text field
    TEXT_READ_ONLY = "text_read_only", _(
        "Text (read-only): Simple Text input, but cannot be edited."
    )
    # Same as text, but has autocomplete for password managers
    USERNAME = (
        "username",
        _(("Username: Same as Text input, but checks for " "and prevents duplicate usernames.")),
    )
    EMAIL = "email", _("Email: Text field with Email type.")
    PASSWORD = (
        "password",  # noqa # nosec
        _(
            (
                "Password: Masked input, password is validated against sources. Policies still "
                "have to be applied to this Stage. If two of these are used in the same stage, "
                "they are ensured to be identical."
            )
        ),
    )
    NUMBER = "number"
    CHECKBOX = "checkbox"
    DATE = "date"
    DATE_TIME = "date-time"

    SEPARATOR = "separator", _("Separator: Static Separator Line")
    HIDDEN = "hidden", _("Hidden: Hidden field, can be used to insert data into form.")
    STATIC = "static", _("Static: Static value, displayed as-is.")


class Prompt(SerializerModel):
    """Single Prompt, part of a prompt stage."""

    prompt_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    field_key = models.TextField(
        help_text=_("Name of the form field, also used to store the value")
    )
    label = models.TextField()
    type = models.CharField(max_length=100, choices=FieldTypes.choices)
    required = models.BooleanField(default=True)
    placeholder = models.TextField(blank=True)
    sub_text = models.TextField(blank=True, default="")

    order = models.IntegerField(default=0)

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.prompt.api import PromptSerializer

        return PromptSerializer

    def field(self, default: Optional[Any]) -> CharField:
        """Get field type for Challenge and response"""
        field_class = CharField
        kwargs = {
            "required": self.required,
        }
        if self.type == FieldTypes.TEXT:
            kwargs["trim_whitespace"] = False
        if self.type == FieldTypes.TEXT_READ_ONLY:
            field_class = ReadOnlyField
        if self.type == FieldTypes.EMAIL:
            field_class = EmailField
        if self.type == FieldTypes.NUMBER:
            field_class = IntegerField
        if self.type == FieldTypes.HIDDEN:
            field_class = HiddenField
            kwargs["required"] = False
            kwargs["default"] = self.placeholder
        if self.type == FieldTypes.CHECKBOX:
            field_class = BooleanField
            kwargs["required"] = False
        if self.type == FieldTypes.DATE:
            field_class = DateField
        if self.type == FieldTypes.DATE_TIME:
            field_class = DateTimeField
        if self.type == FieldTypes.STATIC:
            kwargs["default"] = self.placeholder
            kwargs["required"] = False
            kwargs["label"] = ""
        if self.type == FieldTypes.SEPARATOR:
            kwargs["required"] = False
            kwargs["label"] = ""
        if default:
            kwargs["default"] = default
        return field_class(**kwargs)

    def save(self, *args, **kwargs):
        if self.type not in FieldTypes:
            raise ValueError
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Prompt field '{self.field_key}' type {self.type}"

    class Meta:

        verbose_name = _("Prompt")
        verbose_name_plural = _("Prompts")


class PromptStage(Stage):
    """Define arbitrary prompts for the user."""

    fields = models.ManyToManyField(Prompt)

    validation_policies = models.ManyToManyField(Policy, blank=True)

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.prompt.api import PromptStageSerializer

        return PromptStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.prompt.stage import PromptStageView

        return PromptStageView

    @property
    def component(self) -> str:
        return "ak-stage-prompt-form"

    class Meta:

        verbose_name = _("Prompt Stage")
        verbose_name_plural = _("Prompt Stages")
