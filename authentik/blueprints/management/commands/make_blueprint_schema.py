"""Generate JSON Schema for blueprints"""
from json import dumps
from typing import Any

from django.core.management.base import BaseCommand, no_translations
from django.db.models import Model
from drf_jsonschema_serializer.convert import field_to_converter
from rest_framework.fields import Field, JSONField, UUIDField
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.blueprints.v1.common import BlueprintEntryDesiredState
from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT, is_model_allowed
from authentik.blueprints.v1.meta.registry import BaseMetaModel, registry
from authentik.lib.models import SerializerModel

LOGGER = get_logger()


class Command(BaseCommand):
    """Generate JSON Schema for blueprints"""

    schema: dict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schema = {
            "$schema": "http://json-schema.org/draft-07/schema",
            "$id": "https://goauthentik.io/blueprints/schema.json",
            "type": "object",
            "title": "authentik Blueprint schema",
            "required": ["version", "entries"],
            "properties": {
                "version": {
                    "$id": "#/properties/version",
                    "type": "integer",
                    "title": "Blueprint version",
                    "default": 1,
                },
                "metadata": {
                    "$id": "#/properties/metadata",
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                        "labels": {"type": "object", "additionalProperties": {"type": "string"}},
                    },
                },
                "context": {
                    "$id": "#/properties/context",
                    "type": "object",
                    "additionalProperties": True,
                },
                "entries": {
                    "type": "array",
                    "items": {
                        "oneOf": [],
                    },
                },
            },
            "$defs": {},
        }

    @no_translations
    def handle(self, *args, **options):
        """Generate JSON Schema for blueprints"""
        self.build()
        self.stdout.write(dumps(self.schema, indent=4, default=Command.json_default))

    @staticmethod
    def json_default(value: Any) -> Any:
        """Helper that handles gettext_lazy strings that JSON doesn't handle"""
        return str(value)

    def build(self):
        """Build all models into the schema"""
        for model in registry.get_models():
            if issubclass(model, BaseMetaModel):
                serializer_class = model.serializer()
            else:
                if model._meta.abstract:
                    continue
                if not is_model_allowed(model):
                    continue
                model_instance: Model = model()
                if not isinstance(model_instance, SerializerModel):
                    continue
                serializer_class = model_instance.serializer
            serializer = serializer_class(
                context={
                    SERIALIZER_CONTEXT_BLUEPRINT: False,
                }
            )
            model_path = f"{model._meta.app_label}.{model._meta.model_name}"
            self.schema["properties"]["entries"]["items"]["oneOf"].append(
                self.template_entry(model_path, serializer)
            )

    def template_entry(self, model_path: str, serializer: Serializer) -> dict:
        """Template entry for a single model"""
        model_schema = self.to_jsonschema(serializer)
        model_schema["required"] = []
        def_name = f"model_{model_path}"
        def_path = f"#/$defs/{def_name}"
        self.schema["$defs"][def_name] = model_schema
        return {
            "type": "object",
            "required": ["model", "identifiers"],
            "properties": {
                "model": {"const": model_path},
                "id": {"type": "string"},
                "state": {
                    "type": "string",
                    "enum": [s.value for s in BlueprintEntryDesiredState],
                    "default": "present",
                },
                "conditions": {"type": "array", "items": {"type": "boolean"}},
                "attrs": {"$ref": def_path},
                "identifiers": {"$ref": def_path},
            },
        }

    def field_to_jsonschema(self, field: Field) -> dict:
        """Convert a single field to json schema"""
        if isinstance(field, Serializer):
            result = self.to_jsonschema(field)
        else:
            try:
                converter = field_to_converter[field]
                result = converter.convert(field)
            except KeyError:
                if isinstance(field, JSONField):
                    result = {"type": "object", "additionalProperties": True}
                elif isinstance(field, UUIDField):
                    result = {"type": "string", "format": "uuid"}
                else:
                    raise
        if field.label:
            result["title"] = field.label
        if field.help_text:
            result["description"] = field.help_text
        return self.clean_result(result)

    def clean_result(self, result: dict) -> dict:
        """Remove enumNames from result, recursively"""
        result.pop("enumNames", None)
        for key, value in result.items():
            if isinstance(value, dict):
                result[key] = self.clean_result(value)
        return result

    def to_jsonschema(self, serializer: Serializer) -> dict:
        """Convert serializer to json schema"""
        properties = {}
        required = []
        for name, field in serializer.fields.items():
            if field.read_only:
                continue
            sub_schema = self.field_to_jsonschema(field)
            if field.required:
                required.append(name)
            properties[name] = sub_schema

        result = {"type": "object", "properties": properties}
        if required:
            result["required"] = required
        return result
