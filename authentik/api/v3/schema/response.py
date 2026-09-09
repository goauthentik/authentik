from typing import Any

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
from structlog.stdlib import get_logger

from authentik.api.v3.schema.pagination import PAGINATION
from authentik.api.v3.schema.query import QUERY_PARAMS

LOGGER = get_logger()

GENERIC_ERROR = ResolvedComponent(
    name="GenericError",
    type=ResolvedComponent.SCHEMA,
    object="GenericError",
    schema=build_object_type(
        description=_("Generic API Error"),
        properties={
            "detail": build_basic_type(OpenApiTypes.STR),
            "code": build_basic_type(OpenApiTypes.STR),
        },
        required=["detail"],
    ),
)
GENERIC_ERROR_RESPONSE = ResolvedComponent(
    name="GenericErrorResponse",
    type=ResolvedComponent.RESPONSE,
    object="GenericErrorResponse",
    schema={
        "content": {"application/json": {"schema": GENERIC_ERROR.ref}},
        "description": "",
    },
)
VALIDATION_ERROR = ResolvedComponent(
    "ValidationError",
    object="ValidationError",
    type=ResolvedComponent.SCHEMA,
    schema=build_object_type(
        description=_("Validation Error"),
        properties={
            api_settings.NON_FIELD_ERRORS_KEY: build_array_type(build_basic_type(OpenApiTypes.STR)),
            "code": build_basic_type(OpenApiTypes.STR),
        },
        required=[],
        additionalProperties={},
    ),
)
VALIDATION_ERROR_RESPONSE = ResolvedComponent(
    name="ValidationErrorResponse",
    type=ResolvedComponent.RESPONSE,
    object="ValidationErrorResponse",
    schema={
        "content": {
            "application/json": {
                "schema": VALIDATION_ERROR.ref,
            }
        },
        "description": "",
    },
)


def postprocess_schema_register(
    result: dict[str, Any], generator: SchemaGenerator, **kwargs
) -> dict[str, Any]:
    """Register custom schema components"""
    LOGGER.debug("Registering custom schemas")
    generator.registry.register_on_missing(PAGINATION)
    generator.registry.register_on_missing(GENERIC_ERROR)
    generator.registry.register_on_missing(GENERIC_ERROR_RESPONSE)
    generator.registry.register_on_missing(VALIDATION_ERROR)
    generator.registry.register_on_missing(VALIDATION_ERROR_RESPONSE)
    for query in QUERY_PARAMS.values():
        generator.registry.register_on_missing(query)
    return result


def postprocess_schema_responses(
    result: dict[str, Any], generator: SchemaGenerator, **kwargs
) -> dict[str, Any]:
    """Default error responses"""
    LOGGER.debug("Adding default error responses")
    for path in result["paths"].values():
        for method in path.values():
            method["responses"].setdefault("400", VALIDATION_ERROR_RESPONSE.ref)
            method["responses"].setdefault("403", GENERIC_ERROR_RESPONSE.ref)

    result["components"] = generator.registry.build(spectacular_settings.APPEND_COMPONENTS)

    # This is a workaround for authentik/stages/prompt/stage.py
    # since the serializer PromptChallengeResponse
    # accepts dynamic keys
    for component in result["components"]["schemas"]:
        if component == "PromptChallengeResponseRequest":
            comp = result["components"]["schemas"][component]
            comp["additionalProperties"] = {}
    return result
