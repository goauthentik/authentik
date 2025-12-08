"""DjangoQL search"""

from collections import OrderedDict, defaultdict
from collections.abc import Generator

from django.db import connection
from django.db.models import Model, Q
from akql.compat import text_type
from akql.schema import StrField


class JSONSearchField(StrField):
    """JSON field for DjangoQL"""

    model: Model

    def __init__(self, model=None, name=None, nullable=None, suggest_nested=True):
        # Set this in the constructor to not clobber the type variable
        self.type = "relation"
        self.suggest_nested = suggest_nested
        super().__init__(model, name, nullable)

    def get_lookup(self, path, operator, value):
        search = "__".join(path)
        op, invert = self.get_operator(operator)
        q = Q(**{f"{search}{op}": self.get_lookup_value(value)})
        return ~q if invert else q

    def json_field_keys(self) -> Generator[tuple[str]]:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                WITH RECURSIVE "{self.name}_keys" AS (
                    SELECT
                        ARRAY[jsonb_object_keys("{self.name}")] AS key_path_array,
                        "{self.name}" -> jsonb_object_keys("{self.name}") AS value
                    FROM {self.model._meta.db_table}
                    WHERE "{self.name}" IS NOT NULL
                        AND jsonb_typeof("{self.name}") = 'object'

                    UNION ALL

                    SELECT
                        ck.key_path_array || jsonb_object_keys(ck.value),
                        ck.value -> jsonb_object_keys(ck.value) AS value
                    FROM "{self.name}_keys" ck
                    WHERE jsonb_typeof(ck.value) = 'object'
                ),

                unique_paths AS (
                    SELECT DISTINCT key_path_array
                    FROM "{self.name}_keys"
                )

                SELECT key_path_array FROM unique_paths;
            """  # nosec
            )
            return (x[0] for x in cursor.fetchall())

    def get_nested_options(self) -> OrderedDict:
        """Get keys of all nested objects to show autocomplete"""
        if not self.suggest_nested:
            return OrderedDict()
        base_model_name = f"{self.model._meta.app_label}.{self.model._meta.model_name}_{self.name}"

        def recursive_function(parts: list[str], parent_parts: list[str] | None = None):
            if not parent_parts:
                parent_parts = []
            path = parts.pop(0)
            parent_parts.append(path)
            relation_key = "_".join(parent_parts)
            if len(parts) > 1:
                out_dict = {
                    relation_key: {
                        parts[0]: {
                            "type": "relation",
                            "relation": f"{relation_key}_{parts[0]}",
                        }
                    }
                }
                child_paths = recursive_function(parts.copy(), parent_parts.copy())
                child_paths.update(out_dict)
                return child_paths
            else:
                return {relation_key: {parts[0]: {}}}

        relation_structure = defaultdict(dict)

        for relations in self.json_field_keys():
            result = recursive_function([base_model_name] + relations)
            for relation_key, value in result.items():
                for sub_relation_key, sub_value in value.items():
                    if not relation_structure[relation_key].get(sub_relation_key, None):
                        relation_structure[relation_key][sub_relation_key] = sub_value
                    else:
                        relation_structure[relation_key][sub_relation_key].update(sub_value)

        final_dict = defaultdict(dict)

        for key, value in relation_structure.items():
            for sub_key, sub_value in value.items():
                if not sub_value:
                    final_dict[key][sub_key] = {
                        "type": "str",
                        "nullable": True,
                    }
                else:
                    final_dict[key][sub_key] = sub_value
        return OrderedDict(final_dict)

    def relation(self) -> str:
        return f"{self.model._meta.app_label}.{self.model._meta.model_name}_{self.name}"


class ChoiceSearchField(StrField):
    def __init__(self, model=None, name=None, nullable=None):
        super().__init__(model, name, nullable, suggest_options=True)

    def get_options(self, search):
        result = []
        choices = self._field_choices()
        if choices:
            search = search.lower()
            for c in choices:
                choice = text_type(c[0])
                if search in choice.lower():
                    result.append(choice)
        return result
