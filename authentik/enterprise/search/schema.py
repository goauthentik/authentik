from drf_spectacular.generators import SchemaGenerator

from authentik.api.schema import create_component
from authentik.enterprise.search.ql import AUTOCOMPLETE_COMPONENT_NAME, AUTOCOMPLETE_SCHEMA


def postprocess_schema_search_autocomplete(result, generator: SchemaGenerator, **kwargs):
    create_component(generator, AUTOCOMPLETE_COMPONENT_NAME, AUTOCOMPLETE_SCHEMA)

    return result
