from django.utils.translation import gettext_lazy as _
from drf_spectacular.plumbing import (
    ResolvedComponent,
    build_array_type,
    build_basic_type,
    build_object_type,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework.settings import api_settings

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
PAGINATION = ResolvedComponent(
    name="Pagination",
    type=ResolvedComponent.SCHEMA,
    object="Pagination",
    schema=build_object_type(
        properties={
            "next": build_basic_type(OpenApiTypes.NUMBER),
            "previous": build_basic_type(OpenApiTypes.NUMBER),
            "count": build_basic_type(OpenApiTypes.NUMBER),
            "current": build_basic_type(OpenApiTypes.NUMBER),
            "total_pages": build_basic_type(OpenApiTypes.NUMBER),
            "start_index": build_basic_type(OpenApiTypes.NUMBER),
            "end_index": build_basic_type(OpenApiTypes.NUMBER),
        },
        required=[
            "next",
            "previous",
            "count",
            "current",
            "total_pages",
            "start_index",
            "end_index",
        ],
    ),
)
