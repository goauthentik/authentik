from collections import OrderedDict

from akql.schema import JSONSearchField, RelationField


class AKQLSchemaSerializer:
    def serialize(self, schema):
        models = {}
        for model_label, fields in schema.models.items():
            models[model_label] = OrderedDict(
                [(name, self.serialize_field(f)) for name, f in fields.items()],
            )
        return {
            "current_model": schema.model_label(schema.current_model),
            "models": models,
        }

    def serialize_field(self, field):
        result = {
            "type": field.type,
            "nullable": field.nullable,
            "options": self.serialize_field_options(field),
        }
        if isinstance(field, RelationField):
            result["relation"] = field.relation
        if isinstance(field, JSONSearchField):
            result["relation"] = field.relation()
        return result

    def serialize_field_options(self, field):
        return list(field.get_options("")) if field.suggest_options else None
