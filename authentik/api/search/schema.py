from djangoql.serializers import DjangoQLSchemaSerializer

from authentik.api.search.fields import JSONSearchField


class AKQLSchemaSerializer(DjangoQLSchemaSerializer):
    def serialize(self, schema):
        serialization = super().serialize(schema)
        for _, fields in schema.models.items():
            for _, field in fields.items():
                if not isinstance(field, JSONSearchField):
                    continue
                serialization["models"].update(field.get_nested_options(self))
        return serialization

    def serialize_field(self, field):
        result = super().serialize_field(field)
        if isinstance(field, JSONSearchField):
            result["relation"] = field.relation()
        return result
