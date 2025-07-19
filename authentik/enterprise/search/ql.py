"""DjangoQL search"""

from django.apps import apps
from django.db.models import QuerySet
from djangoql.ast import Name
from djangoql.exceptions import DjangoQLError
from djangoql.queryset import apply_search
from djangoql.schema import DjangoQLSchema
from rest_framework.filters import SearchFilter
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.enterprise.search.fields import JSONSearchField

LOGGER = get_logger()
AUTOCOMPLETE_COMPONENT_NAME = "Autocomplete"
AUTOCOMPLETE_SCHEMA = {
    "type": "object",
    "additionalProperties": {},
}


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


# Inherits from SearchFilter to keep the schema correctly
class QLSearch(SearchFilter):
    """rest_framework search filter which uses DjangoQL"""

    def __init__(self):
        super().__init__()
        self._fallback = SearchFilter()

    @property
    def enabled(self):
        return apps.get_app_config("authentik_enterprise").enabled()

    def get_search_terms(self, request: Request) -> str:
        """Search terms are set by a ?search=... query parameter,
        and may be comma and/or whitespace delimited."""
        params = request.query_params.get("search", "")
        params = params.replace("\x00", "")  # strip null characters
        return params

    def get_schema(self, request: Request, view) -> BaseSchema:
        ql_fields = []
        if hasattr(view, "get_ql_fields"):
            ql_fields = view.get_ql_fields()

        class InlineSchema(BaseSchema):
            def get_fields(self, model):
                return ql_fields or []

        return InlineSchema

    def filter_queryset(self, request: Request, queryset: QuerySet, view) -> QuerySet:
        search_query = self.get_search_terms(request)
        schema = self.get_schema(request, view)
        if len(search_query) == 0 or not self.enabled:
            return self._fallback.filter_queryset(request, queryset, view)
        try:
            return apply_search(queryset, search_query, schema=schema)
        except DjangoQLError as exc:
            LOGGER.debug("Failed to parse search expression", exc=exc)
            return self._fallback.filter_queryset(request, queryset, view)
