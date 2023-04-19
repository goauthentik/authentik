"""prompt models"""
from typing import Any, Optional, Type
from urllib.parse import urlparse, urlunparse
from uuid import uuid4

from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    DateField,
    DateTimeField,
    EmailField,
    HiddenField,
    IntegerField,
    ReadOnlyField,
)
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.core.expression.evaluator import PropertyMappingEvaluator
from authentik.core.models import User
from authentik.flows.models import Stage
from authentik.lib.models import SerializerModel
from authentik.policies.models import Policy

CHOICES_CONTEXT_SUFFIX = "__choices"

LOGGER = get_logger()


class FieldTypes(models.TextChoices):
    """Field types an Prompt can be"""

    # update website/docs/flow/stages/prompt/index.md

    # Simple text field
    TEXT = "text", _("Text: Simple Text input")
    # Long text field
    TEXT_AREA = "text_area", _("Text area: Multiline Text Input.")
    # Simple text field
    TEXT_READ_ONLY = "text_read_only", _(
        "Text (read-only): Simple Text input, but cannot be edited."
    )
    # Long text field
    TEXT_AREA_READ_ONLY = "text_area_read_only", _(
        "Text area (read-only): Multiline Text input, but cannot be edited."
    )

    # Same as text, but has autocomplete for password managers
    USERNAME = (
        "username",
        _("Username: Same as Text input, but checks for and prevents duplicate usernames."),
    )
    EMAIL = "email", _("Email: Text field with Email type.")
    PASSWORD = (
        "password",  # noqa # nosec
        _(
            "Password: Masked input, multiple inputs of this type on the same prompt "
            "need to be identical."
        ),
    )
    NUMBER = "number"
    CHECKBOX = "checkbox"
    RADIO_BUTTON_GROUP = "radio-button-group", _(
        "Fixed choice field rendered as a group of radio buttons."
    )
    DROPDOWN = "dropdown", _("Fixed choice field rendered as a dropdown.")
    DATE = "date"
    DATE_TIME = "date-time"

    FILE = (
        "file",
        _(
            "File: File upload for arbitrary files. File content will be available in flow "
            "context as data-URI"
        ),
    )

    SEPARATOR = "separator", _("Separator: Static Separator Line")
    HIDDEN = "hidden", _("Hidden: Hidden field, can be used to insert data into form.")
    STATIC = "static", _("Static: Static value, displayed as-is.")

    AK_LOCALE = "ak-locale", _("authentik: Selection of locales authentik supports")


CHOICE_FIELDS = (FieldTypes.RADIO_BUTTON_GROUP, FieldTypes.DROPDOWN)


class InlineFileField(CharField):
    """Field for inline data-URI base64 encoded files"""

    def to_internal_value(self, data: str):
        uri = urlparse(data)
        if uri.scheme != "data":
            raise ValidationError("Invalid scheme")
        header, _encoded = uri.path.split(",", 1)
        _mime, _, enc = header.partition(";")
        if enc != "base64":
            raise ValidationError("Invalid encoding")
        return super().to_internal_value(urlunparse(uri))


class Prompt(SerializerModel):
    """Single Prompt, part of a prompt stage."""

    prompt_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.TextField(unique=True, blank=False)

    field_key = models.TextField(
        help_text=_("Name of the form field, also used to store the value")
    )
    label = models.TextField()
    type = models.CharField(max_length=100, choices=FieldTypes.choices)
    required = models.BooleanField(default=True)
    placeholder = models.TextField(
        blank=True,
        help_text=_(
            "Optionally provide a short hint that describes the expected input value. "
            "When creating a fixed choice field, enable interpreting as "
            "expression and return a list to return multiple choices."
        ),
    )
    initial_value = models.TextField(
        blank=True,
        help_text=_(
            "Optionally pre-fill the input with an initial value. "
            "When creating a fixed choice field, enable interpreting as "
            "expression and return a list to return multiple default choices."
        ),
    )
    sub_text = models.TextField(blank=True, default="")

    order = models.IntegerField(default=0)

    placeholder_expression = models.BooleanField(default=False)
    initial_value_expression = models.BooleanField(default=False)

    @property
    def serializer(self) -> Type[BaseSerializer]:
        from authentik.stages.prompt.api import PromptSerializer

        return PromptSerializer

    def get_choices(
        self,
        prompt_context: dict,
        user: User,
        request: HttpRequest,
        dry_run: Optional[bool] = False,
    ) -> Optional[tuple[dict[str, Any]]]:
        """Get fully interpolated list of choices"""
        if self.type not in CHOICE_FIELDS:
            return None

        raw_choices = self.placeholder

        if self.field_key + CHOICES_CONTEXT_SUFFIX in prompt_context:
            raw_choices = prompt_context[self.field_key + CHOICES_CONTEXT_SUFFIX]
        elif self.placeholder_expression:
            evaluator = PropertyMappingEvaluator(
                self, user, request, prompt_context=prompt_context, dry_run=dry_run
            )
            try:
                raw_choices = evaluator.evaluate(self.placeholder)
            except Exception as exc:  # pylint:disable=broad-except
                wrapped = PropertyMappingExpressionException(str(exc))
                LOGGER.warning(
                    "failed to evaluate prompt choices",
                    exc=wrapped,
                )
                if dry_run:
                    raise wrapped from exc

        if isinstance(raw_choices, (list, tuple, set)):
            choices = raw_choices
        else:
            choices = [raw_choices]

        if len(choices) == 0:
            LOGGER.warning("failed to get prompt choices", choices=choices, input=raw_choices)

        return tuple(choices)

    def get_placeholder(
        self,
        prompt_context: dict,
        user: User,
        request: HttpRequest,
        dry_run: Optional[bool] = False,
    ) -> str:
        """Get fully interpolated placeholder"""
        if self.type in CHOICE_FIELDS:
            # Choice fields use the placeholder to define all valid choices.
            # Therefore their actual placeholder is always blank
            return ""

        if self.placeholder_expression:
            evaluator = PropertyMappingEvaluator(
                self, user, request, prompt_context=prompt_context, dry_run=dry_run
            )
            try:
                return evaluator.evaluate(self.placeholder)
            except Exception as exc:  # pylint:disable=broad-except
                wrapped = PropertyMappingExpressionException(str(exc))
                LOGGER.warning(
                    "failed to evaluate prompt placeholder",
                    exc=wrapped,
                )
                if dry_run:
                    raise wrapped from exc
        return self.placeholder

    def get_initial_value(
        self,
        prompt_context: dict,
        user: User,
        request: HttpRequest,
        dry_run: Optional[bool] = False,
    ) -> str:
        """Get fully interpolated initial value"""

        if self.field_key in prompt_context:
            # We don't want to parse this as an expression since a user will
            # be able to control the input
            value = prompt_context[self.field_key]
        elif self.initial_value_expression:
            evaluator = PropertyMappingEvaluator(
                self, user, request, prompt_context=prompt_context, dry_run=dry_run
            )
            try:
                value = evaluator.evaluate(self.initial_value)
            except Exception as exc:  # pylint:disable=broad-except
                wrapped = PropertyMappingExpressionException(str(exc))
                LOGGER.warning(
                    "failed to evaluate prompt initial value",
                    exc=wrapped,
                )
                if dry_run:
                    raise wrapped from exc
                value = self.initial_value
        else:
            value = self.initial_value

        if self.type in CHOICE_FIELDS:
            # Ensure returned value is a valid choice
            choices = self.get_choices(prompt_context, user, request)
            if not choices:
                return ""
            if value not in choices:
                return choices[0]

        return value

    def field(self, default: Optional[Any], choices: Optional[list[Any]] = None) -> CharField:
        """Get field type for Challenge and response. Choices are only valid for CHOICE_FIELDS."""
        field_class = CharField
        kwargs = {
            "required": self.required,
        }
        if self.type in (FieldTypes.TEXT, FieldTypes.TEXT_AREA):
            kwargs["trim_whitespace"] = False
            kwargs["allow_blank"] = not self.required
        if self.type in (FieldTypes.TEXT_READ_ONLY, FieldTypes.TEXT_AREA_READ_ONLY):
            field_class = ReadOnlyField
            # required can't be set for ReadOnlyField
            kwargs["required"] = False
        if self.type == FieldTypes.EMAIL:
            field_class = EmailField
            kwargs["allow_blank"] = not self.required
        if self.type == FieldTypes.NUMBER:
            field_class = IntegerField
        if self.type == FieldTypes.CHECKBOX:
            field_class = BooleanField
            kwargs["required"] = False
        if self.type in CHOICE_FIELDS:
            field_class = ChoiceField
            kwargs["choices"] = choices or []
        if self.type == FieldTypes.DATE:
            field_class = DateField
        if self.type == FieldTypes.DATE_TIME:
            field_class = DateTimeField
        if self.type == FieldTypes.FILE:
            field_class = InlineFileField
        if self.type == FieldTypes.SEPARATOR:
            kwargs["required"] = False
            kwargs["label"] = ""
        if self.type == FieldTypes.HIDDEN:
            field_class = HiddenField
            kwargs["required"] = False
            kwargs["default"] = self.placeholder
        if self.type == FieldTypes.STATIC:
            kwargs["default"] = self.placeholder
            kwargs["required"] = False
            kwargs["label"] = ""

        if self.type == FieldTypes.AK_LOCALE:
            kwargs["allow_blank"] = True

        if default:
            kwargs["default"] = default
        # May not set both `required` and `default`
        if "default" in kwargs:
            kwargs.pop("required", None)
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
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.prompt.api import PromptStageSerializer

        return PromptStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.prompt.stage import PromptStageView

        return PromptStageView

    @property
    def component(self) -> str:
        return "ak-stage-prompt-form"

    class Meta:
        verbose_name = _("Prompt Stage")
        verbose_name_plural = _("Prompt Stages")
