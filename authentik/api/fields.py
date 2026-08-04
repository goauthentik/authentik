"""Shared DRF serializer fields for the authentik API."""

from typing import Any

from django.db.models import Field as ModelField
from rest_framework.fields import ChoiceField


class GeneratedEnumChoiceField(ChoiceField):
    """ChoiceField whose labels are stable UI identifiers (no translation).

    Opt into OpenAPI ``x-enum-varnames`` so the generated TypeScript client can
    drive admin UI options for vendor names, algorithm identifiers, and similar
    non-translated choice sets.
    """

    @classmethod
    def from_model_field(cls, model_field: ModelField, **kwargs: Any):
        """Build a field that preserves the model field's required/default/null."""
        field_kwargs: dict[str, Any] = {
            "choices": model_field.choices,
            "required": not (model_field.has_default() or model_field.blank or model_field.null),
            "allow_null": bool(model_field.null),
            "allow_blank": bool(getattr(model_field, "blank", False)),
        }
        if model_field.has_default() and not callable(model_field.default):
            field_kwargs["default"] = model_field.default
        if model_field.verbose_name:
            field_kwargs["label"] = model_field.verbose_name
        if model_field.help_text:
            field_kwargs["help_text"] = model_field.help_text
        field_kwargs.update(kwargs)
        return cls(**field_kwargs)
