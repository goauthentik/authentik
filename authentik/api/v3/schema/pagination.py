from drf_spectacular.plumbing import (
    ResolvedComponent,
    build_basic_type,
    build_object_type,
)
from drf_spectacular.types import OpenApiTypes

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
