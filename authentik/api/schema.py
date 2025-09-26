"""Error Response schema, from https://github.com/axnsan12/drf-yasg/issues/224"""

from collections.abc import Callable
from typing import Any

from django.utils.translation import gettext_lazy as _
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.plumbing import (
    ResolvedComponent,
    build_array_type,
    build_basic_type,
    build_object_type,
)
from drf_spectacular.renderers import OpenApiJsonRenderer
from drf_spectacular.settings import spectacular_settings
from drf_spectacular.types import OpenApiTypes
from rest_framework.settings import api_settings

from authentik.api.apps import AuthentikAPIConfig
from authentik.api.pagination import PAGINATION_COMPONENT_NAME, PAGINATION_SCHEMA

GENERIC_ERROR = build_object_type(
    description=_("Generic API Error"),
    properties={
        "detail": build_basic_type(OpenApiTypes.STR),
        "code": build_basic_type(OpenApiTypes.STR),
    },
    required=["detail"],
)
VALIDATION_ERROR = build_object_type(
    description=_("Validation Error"),
    properties={
        api_settings.NON_FIELD_ERRORS_KEY: build_array_type(build_basic_type(OpenApiTypes.STR)),
        "code": build_basic_type(OpenApiTypes.STR),
    },
    required=[],
    additionalProperties={},
)


def create_component(
    generator: SchemaGenerator, name: str, schema: Any, type_=ResolvedComponent.SCHEMA
) -> ResolvedComponent:
    """Register a component and return a reference to it."""
    component = ResolvedComponent(
        name=name,
        type=type_,
        schema=schema,
        object=name,
    )
    generator.registry.register_on_missing(component)
    return component


def preprocess_schema_exclude_non_api(endpoints: list[tuple[str, Any, Any, Callable]], **kwargs):
    """Filter out all API Views which are not mounted under /api"""
    return [
        (path, path_regex, method, callback)
        for path, path_regex, method, callback in endpoints
        if path.startswith("/" + AuthentikAPIConfig.mountpoint)
    ]


def postprocess_schema_responses(
    result: dict[str, Any], generator: SchemaGenerator, **kwargs
) -> dict[str, Any]:
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


def postprocess_schema_query_params(
    result: dict[str, Any], generator: SchemaGenerator, **kwargs
) -> dict[str, Any]:
    """Optimise pagination parameters, instead of redeclaring parameters for each endpoint
    declare them globally and refer to them"""
    to_replace = {
        "ordering": create_component(
            generator,
            "QueryPaginationOrdering",
            {
                "name": "ordering",
                "required": False,
                "in": "query",
                "description": "Which field to use when ordering the results.",
                "schema": {"type": "string"},
            },
            ResolvedComponent.PARAMETER,
        ),
        "page": create_component(
            generator,
            "QueryPaginationPage",
            {
                "name": "page",
                "required": False,
                "in": "query",
                "description": "A page number within the paginated result set.",
                "schema": {"type": "integer"},
            },
            ResolvedComponent.PARAMETER,
        ),
        "page_size": create_component(
            generator,
            "QueryPaginationPageSize",
            {
                "name": "page_size",
                "required": False,
                "in": "query",
                "description": "Number of results to return per page.",
                "schema": {"type": "integer"},
            },
            ResolvedComponent.PARAMETER,
        ),
        "search": create_component(
            generator,
            "QuerySearch",
            {
                "name": "search",
                "required": False,
                "in": "query",
                "description": "A search term.",
                "schema": {"type": "string"},
            },
            ResolvedComponent.PARAMETER,
        ),
        # Not related to pagination but a very common query param
        "name": create_component(
            generator,
            "QueryName",
            {
                "name": "name",
                "in": "query",
                "schema": {"type": "string"},
            },
            ResolvedComponent.PARAMETER,
        ),
    }
    for path in result["paths"].values():
        for method in path.values():
            for idx, param in enumerate(method.get("parameters", [])):
                for replace_name, replace_ref in to_replace.items():
                    if param["name"] == replace_name:
                        method["parameters"][idx] = replace_ref.ref
    return result


def postprocess_schema_remove_unused(
    result: dict[str, Any], generator: SchemaGenerator, **kwargs
) -> dict[str, Any]:
    """Remove unused components"""
    # To check if the schema is used, render it to JSON and then substring check that
    # less efficient than walking through the tree but a lot simpler and no
    # possibility that we miss something
    raw = OpenApiJsonRenderer().render(result, renderer_context={}).decode()
    for key in result["components"][ResolvedComponent.SCHEMA].keys():
        schema_usages = raw.count(f"#/components/{ResolvedComponent.SCHEMA}/{key}")
        if schema_usages >= 1:
            continue
        del generator.registry[(key, ResolvedComponent.SCHEMA)]
    result["components"] = generator.registry.build(spectacular_settings.APPEND_COMPONENTS)
    return result


def postprocess_schema_simplify_paginated(
    result: dict[str, Any], generator: SchemaGenerator, **kwargs
) -> dict[str, Any]:
    prefix = "#/components/schemas/Paginated"
    for _path, path in result["paths"].items():
        for _method, method in path.items():
            for _code, response in method["responses"].items():
                if "content" not in response:
                    continue
                for _content_type, content_response in response["content"].items():
                    content_schema = content_response.get("schema", {})
                    ref: str | None = content_schema.get("$ref", None)
                    if not ref:
                        continue
                    if not ref.startswith(prefix):
                        continue
                    actual_component = generator.registry[
                        (ref.replace(prefix, "").replace("List", ""), ResolvedComponent.SCHEMA)
                    ]
                    content_response["schema"] = build_object_type(
                        properties={
                            "pagination": {
                                "$ref": f"#/components/schemas/{PAGINATION_COMPONENT_NAME}"
                            },
                            "autocomplete": {"$ref": "#/components/schemas/Autocomplete"},
                            "results": build_array_type(schema={"$ref": actual_component.ref}),
                        },
                        required=["pagination", "results", "autocomplete"],
                    )
    return result
