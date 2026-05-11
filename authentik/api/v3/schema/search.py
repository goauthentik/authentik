from typing import TYPE_CHECKING

from drf_spectacular.plumbing import ResolvedComponent, build_object_type

if TYPE_CHECKING:
    from drf_spectacular.generators import SchemaGenerator


AUTOCOMPLETE_SCHEMA = ResolvedComponent(
    name="Autocomplete",
    object="Autocomplete",
    type=ResolvedComponent.SCHEMA,
    schema=build_object_type(additionalProperties={}),
)


def postprocess_schema_search_autocomplete(result, generator: SchemaGenerator, **kwargs):
    generator.registry.register_on_missing(AUTOCOMPLETE_SCHEMA)

    return result
