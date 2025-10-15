"""Error Response schema, from https://github.com/axnsan12/drf-yasg/issues/224"""

from collections.abc import Callable
from typing import Any

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.plumbing import ResolvedComponent
from drf_spectacular.renderers import OpenApiJsonRenderer
from drf_spectacular.settings import spectacular_settings
from structlog.stdlib import get_logger

from authentik.api.apps import AuthentikAPIConfig
from authentik.api.v3.schema.query import QUERY_PARAMS
from authentik.api.v3.schema.response import (
    GENERIC_ERROR,
    GENERIC_ERROR_RESPONSE,
    PAGINATION,
    VALIDATION_ERROR,
    VALIDATION_ERROR_RESPONSE,
)

LOGGER = get_logger()


def preprocess_schema_exclude_non_api(endpoints: list[tuple[str, Any, Any, Callable]], **kwargs):
    """Filter out all API Views which are not mounted under /api"""
    return [
        (path, path_regex, method, callback)
        for path, path_regex, method, callback in endpoints
        if path.startswith("/" + AuthentikAPIConfig.mountpoint)
    ]


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


def postprocess_schema_query_params(
    result: dict[str, Any], generator: SchemaGenerator, **kwargs
) -> dict[str, Any]:
    """Optimise pagination parameters, instead of redeclaring parameters for each endpoint
    declare them globally and refer to them"""
    LOGGER.debug("Deduplicating query parameters")
    for path in result["paths"].values():
        for method in path.values():
            for idx, param in enumerate(method.get("parameters", [])):
                if param["name"] not in QUERY_PARAMS:
                    continue
                method["parameters"][idx] = QUERY_PARAMS[param["name"]].ref
    return result


def postprocess_schema_remove_unused(
    result: dict[str, Any], generator: SchemaGenerator, **kwargs
) -> dict[str, Any]:
    """Remove unused components"""
    # To check if the schema is used, render it to JSON and then substring check that
    # less efficient than walking through the tree but a lot simpler and no
    # possibility that we miss something
    raw = OpenApiJsonRenderer().render(result, renderer_context={}).decode()
    count = 0
    for key in result["components"][ResolvedComponent.SCHEMA].keys():
        schema_usages = raw.count(f"#/components/{ResolvedComponent.SCHEMA}/{key}")
        if schema_usages >= 1:
            continue
        del generator.registry[(key, ResolvedComponent.SCHEMA)]
        count += 1
    LOGGER.debug("Removing unused components", count=count)
    result["components"] = generator.registry.build(spectacular_settings.APPEND_COMPONENTS)
    return result
