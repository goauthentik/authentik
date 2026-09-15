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
                # The field is serialized as a relation to this model; make sure the model
                # exists even when no keys are suggested, otherwise the completion client
                # fails resolving the relation and stops offering completions entirely
                serialization["models"].setdefault(field.relation(), {})
        return serialization

    def serialize_field(self, field):
        result = super().serialize_field(field)
        if isinstance(field, JSONSearchField):
            result["relation"] = field.relation()
        return result
