"""Error Response schema, from https://github.com/axnsan12/drf-yasg/issues/224"""
from django.utils.translation import gettext_lazy as _
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.plumbing import (
    ResolvedComponent,
    build_array_type,
    build_basic_type,
    build_object_type,
)
from drf_spectacular.settings import spectacular_settings
from drf_spectacular.types import OpenApiTypes
from rest_framework.settings import api_settings

from authentik.api.pagination import PAGINATION_COMPONENT_NAME, PAGINATION_SCHEMA


def build_standard_type(obj, **kwargs):
    """Build a basic type with optional add owns."""
    schema = build_basic_type(obj)
    schema.update(kwargs)
    return schema


GENERIC_ERROR = build_object_type(
    description=_("Generic API Error"),
    properties={
        "detail": build_standard_type(OpenApiTypes.STR),
        "code": build_standard_type(OpenApiTypes.STR),
    },
    required=["detail"],
)
VALIDATION_ERROR = build_object_type(
    description=_("Validation Error"),
    properties={
        api_settings.NON_FIELD_ERRORS_KEY: build_array_type(build_standard_type(OpenApiTypes.STR)),
        "code": build_standard_type(OpenApiTypes.STR),
    },
    required=[],
    additionalProperties={},
)


def create_component(generator: SchemaGenerator, name, schema, type_=ResolvedComponent.SCHEMA):
    """Register a component and return a reference to it."""
    component = ResolvedComponent(
        name=name,
        type=type_,
        schema=schema,
        object=name,
    )
    generator.registry.register_on_missing(component)
    return component


def postprocess_schema_responses(result, generator: SchemaGenerator, **kwargs):  # noqa: W0613
    """Workaround to set a default response for endpoints.
    Workaround suggested at
    <https://github.com/tfranzel/drf-spectacular/issues/119#issuecomment-656970357>
    for the missing drf-spectacular feature discussed in
    <https://github.com/tfranzel/drf-spectacular/issues/101>.
    """

    create_component(generator, PAGINATION_COMPONENT_NAME, PAGINATION_SCHEMA)

    generic_error = create_component(generator, "GenericError", GENERIC_ERROR)
    validation_error = create_component(generator, "ValidationError", VALIDATION_ERROR)

    for path in result["paths"].values():
        for method in path.values():
            method["responses"].setdefault(
                "400",
                {
                    "content": {
                        "application/json": {
                            "schema": validation_error.ref,
                        }
                    },
                    "description": "",
                },
            )
            method["responses"].setdefault(
                "403",
                {
                    "content": {
                        "application/json": {
                            "schema": generic_error.ref,
                        }
                    },
                    "description": "",
                },
            )

    result["components"] = generator.registry.build(spectacular_settings.APPEND_COMPONENTS)

    # This is a workaround for authentik/stages/prompt/stage.py
    # since the serializer PromptChallengeResponse
    # accepts dynamic keys
    for component in result["components"]["schemas"]:
        if component == "PromptChallengeResponseRequest":
            comp = result["components"]["schemas"][component]
            comp["additionalProperties"] = {}
    return result
