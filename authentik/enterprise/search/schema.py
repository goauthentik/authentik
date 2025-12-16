from akql.schema import JSONSearchField
from akql.serializers import AKQLSchemaSerializer
from drf_spectacular.generators import SchemaGenerator

from authentik.enterprise.search.ql import AUTOCOMPLETE_SCHEMA


class AKQLSchemaSerializer(AKQLSchemaSerializer):
    def serialize(self, schema):
        serialization = super().serialize(schema)
        for _, fields in schema.models.items():
            for _, field in fields.items():
                if not isinstance(field, JSONSearchField):
                    continue
                serialization["models"].update(field.get_nested_options())
        return serialization


def postprocess_schema_search_autocomplete(result, generator: SchemaGenerator, **kwargs):
    generator.registry.register_on_missing(AUTOCOMPLETE_SCHEMA)

    return result
