from djangoql.serializers import DjangoQLSchemaSerializer
from drf_spectacular.generators import SchemaGenerator

from authentik.enterprise.search.fields import JSONSearchField
from authentik.enterprise.search.ql import AUTOCOMPLETE_SCHEMA


class AKQLSchemaSerializer(DjangoQLSchemaSerializer):
    def serialize(self, schema):
        serialization = super().serialize(schema)
        for _, fields in schema.models.items():
            for _, field in fields.items():
                if not isinstance(field, JSONSearchField):
                    continue
                serialization["models"].update(field.get_nested_options())
        return serialization

    def serialize_field(self, field):
        result = super().serialize_field(field)
        if isinstance(field, JSONSearchField):
            result["relation"] = field.relation()
        return result


def postprocess_schema_search_autocomplete(result, generator: SchemaGenerator, **kwargs):
    generator.registry.register_on_missing(AUTOCOMPLETE_SCHEMA)

    return result
