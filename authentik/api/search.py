"""DjangoQL search"""

from collections import OrderedDict

from django.db import models
from django.db.models import QuerySet
from djangoql.ast import Name
from djangoql.compat import text_type
from djangoql.exceptions import DjangoQLError
from djangoql.queryset import apply_search
from djangoql.schema import DjangoQLSchema, StrField
from djangoql.serializers import DjangoQLSchemaSerializer
from rest_framework.filters import SearchFilter
from rest_framework.request import Request
from structlog.stdlib import get_logger

LOGGER = get_logger()
AUTOCOMPLETE_COMPONENT_NAME = "Autocomplete"
AUTOCOMPLETE_SCHEMA = {"type": "object", "additionalProperties": {}}


class JSONSearchField(StrField):
    """JSON field for DjangoQL"""

    model: models.Model
    type = "relation"

    def __init__(self, model=None, name=None, nullable=None):
        super().__init__(model, name, nullable)

    def get_lookup(self, path, operator, value):
        search = "__".join(path)
        op, invert = self.get_operator(operator)
        q = models.Q(**{f"{search}{op}": self.get_lookup_value(value)})
        return ~q if invert else q

    def get_nested_options(self):
        """Get keys of all nested objects to show autocomplete"""
        keys = (
            # self.model.objects.annotate(
            #     keys=models.Func(models.F("user"), function="jsonb_object_keys"),
            #     values=models.Func(models.Expression(), function="jsonb_each"),
            # )
            # .values("keys")
            # .distinct("keys")
            # .order_by("keys")
            # .values_list("keys", flat=True)
            self.model.objects.raw(
                'SELECT event_uuid, key, context->key AS value FROM authentik_events_event, jsonb_object_keys("context") as key;'
            )
        )
        fields = {}
        for evt in keys:
            fields[evt.key] = {
                "type": "str",
                "nullable": False,
                "options": evt.value,
            }
        return fields

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


class BaseSchema(DjangoQLSchema):
    """Base Schema which deals with JSON Fields"""

    def resolve_name(self, name: Name):
        model = self.model_label(self.current_model)
        root_field = name.parts[0]
        field = self.models[model].get(root_field)
        # If the query goes into a JSON field, return the root
        # field as the JSON field will do the rest
        if isinstance(field, JSONSearchField):
            # This is a workaround; build_filter will remove the right-most
            # entry in the path as that is intended to be the same as the field
            # however for JSON that is not the case
            if name.parts[-1] != root_field:
                name.parts.append(root_field)
            return field
        return super().resolve_name(name)


class JSONDjangoQLSchemaSerializer(DjangoQLSchemaSerializer):

    def serialize(self, schema):
        serialization = super().serialize(schema)
        for _, fields in schema.models.items():
            for _, field in fields.items():
                if not isinstance(field, JSONSearchField):
                    continue
                nested_model = OrderedDict()
                for nested_field_name, nested_field in field.get_nested_options().items():
                    # Can't generate a temporary StrField instance here as that requires a
                    # model, and we're only pretending there's a model
                    nested_model[nested_field_name] = nested_field
                serialization["models"][field.relation()] = nested_model
        return serialization

    def serialize_field(self, field):
        result = super().serialize_field(field)
        if isinstance(field, JSONSearchField):
            result["relation"] = field.relation()
        return result


class QLSearch(SearchFilter):
    """rest_framework search filter which uses DjangoQL"""

    def get_search_terms(self, request) -> str:
        """
        Search terms are set by a ?search=... query parameter,
        and may be comma and/or whitespace delimited.
        """
        params = request.query_params.get(self.search_param, "")
        params = params.replace("\x00", "")  # strip null characters
        return params

    def get_schema(self, request: Request, view) -> BaseSchema:
        search_fields = self.get_search_fields(view, request)

        class InlineSchema(BaseSchema):
            def get_fields(self, model):
                fields = []
                if not search_fields:
                    return fields
                for field in search_fields:
                    fields.append(field)
                return fields

        return InlineSchema

    def filter_queryset(self, request: Request, queryset: QuerySet, view) -> QuerySet:
        search_query = self.get_search_terms(request)
        schema = self.get_schema(request, view)
        if len(search_query) == 0:
            return SearchFilter().filter_queryset(request, queryset, view)
        try:
            return apply_search(queryset, search_query, schema=schema)
        except DjangoQLError as exc:
            LOGGER.warning(exc)
            return SearchFilter().filter_queryset(request, queryset, view)
