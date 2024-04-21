"""DjangoQL search"""

from django.db import models
from django.db.models import QuerySet
from djangoql.ast import Name
from djangoql.exceptions import DjangoQLError
from djangoql.queryset import apply_search
from djangoql.schema import DjangoQLSchema, StrField
from rest_framework.fields import JSONField
from rest_framework.filters import SearchFilter
from rest_framework.request import Request
from rest_framework.serializers import ModelSerializer
from structlog.stdlib import get_logger

LOGGER = get_logger()
AUTOCOMPLETE_COMPONENT_NAME = "Autocomplete"
AUTOCOMPLETE_SCHEMA = {"type": "object", "additionalProperties": {}}


class JSONSearchField(StrField):
    """JSON field for DjangoQL"""

    def get_lookup(self, path, operator, value):
        search = "__".join(path)
        op, invert = self.get_operator(operator)
        q = models.Q(**{f"{search}{op}": self.get_lookup_value(value)})
        return ~q if invert else q


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
        serializer: ModelSerializer = view.get_serializer()

        class InlineSchema(BaseSchema):
            def get_fields(self, model):
                fields = []
                if not search_fields:
                    return fields
                for field in search_fields:
                    field_name = field.split("__")[0]
                    serializer_field = serializer.fields.get(field_name)
                    if isinstance(serializer_field, JSONField):
                        fields.append(
                            JSONSearchField(
                                model=model,
                                name=field_name,
                            )
                        )
                    else:
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
