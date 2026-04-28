from typing import Any

from django.utils.translation import gettext_lazy as _
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.plumbing import (
    ResolvedComponent,
    build_basic_type,
    build_parameter_type,
)
from drf_spectacular.types import OpenApiTypes
from structlog.stdlib import get_logger

LOGGER = get_logger()


QUERY_PARAMS = {
    "ordering": ResolvedComponent(
        name="QueryPaginationOrdering",
        type=ResolvedComponent.PARAMETER,
        object="QueryPaginationOrdering",
        schema=build_parameter_type(
            name="ordering",
            schema=build_basic_type(OpenApiTypes.STR),
            location="query",
            description=_("Which field to use when ordering the results."),
        ),
    ),
    "page": ResolvedComponent(
        name="QueryPaginationPage",
        type=ResolvedComponent.PARAMETER,
        object="QueryPaginationPage",
        schema=build_parameter_type(
            name="page",
            schema=build_basic_type(OpenApiTypes.INT),
            location="query",
            description=_("A page number within the paginated result set."),
        ),
    ),
    "page_size": ResolvedComponent(
        name="QueryPaginationPageSize",
        type=ResolvedComponent.PARAMETER,
        object="QueryPaginationPageSize",
        schema=build_parameter_type(
            name="page_size",
            schema=build_basic_type(OpenApiTypes.INT),
            location="query",
            description=_("Number of results to return per page."),
        ),
    ),
    "search": ResolvedComponent(
        name="QuerySearch",
        type=ResolvedComponent.PARAMETER,
        object="QuerySearch",
        schema=build_parameter_type(
            name="search",
            schema=build_basic_type(OpenApiTypes.STR),
            location="query",
            description=_("A search term."),
        ),
    ),
    # Not related to pagination but a very common query param
    "name": ResolvedComponent(
        name="QueryName",
        type=ResolvedComponent.PARAMETER,
        object="QueryName",
        schema=build_parameter_type(
            name="name",
            schema=build_basic_type(OpenApiTypes.STR),
            location="query",
        ),
    ),
}


def postprocess_schema_query_params(
    result: dict[str, Any], generator: SchemaGenerator, **kwargs
) -> dict[str, Any]:
    """Optimize pagination parameters, instead of redeclaring parameters for each endpoint
    declare them globally and refer to them"""
    LOGGER.debug("Deduplicating query parameters")
    for path in result["paths"].values():
        for method in path.values():
            for idx, param in enumerate(method.get("parameters", [])):
                if param["name"] not in QUERY_PARAMS:
                    continue
                method["parameters"][idx] = QUERY_PARAMS[param["name"]].ref
    return result
