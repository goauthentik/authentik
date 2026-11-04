"""DjangoQL search"""

from django.db.models import QuerySet
from django.db.models.constants import LOOKUP_SEP
from djangoql.ast import Name
from djangoql.exceptions import DjangoQLError
from djangoql.parser import DjangoQLParser
from djangoql.queryset import build_filter
from djangoql.schema import DjangoQLSchema
from rest_framework.filters import SearchFilter
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.api.search.fields import JSONSearchField
from authentik.rbac.endpoint_checks import EndpointChecks
from authentik.rbac.field_rules import FieldRules

LOGGER = get_logger()


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


class HiddenFieldsSearchFilter(SearchFilter):
    """This is used to prevent unauthorized users from probing values of fields hidden to them."""

    def __init__(self):
        super().__init__()
        self.hidden_whole_fields: set[str] = set()

    def get_search_fields(self, view, request: Request):
        fields = super().get_search_fields(view, request)
        if not fields or not self.hidden_whole_fields:
            return fields
        return [
            field for field in fields if self.searched_field(field) not in self.hidden_whole_fields
        ]

    def searched_field(self, search_field: str) -> str:
        """The model field a `search_fields` entry starts from, without DRF's lookup prefix
        (`^`, `=`, `@` or `$`) or a `__` path into related models"""
        if search_field[:1] in self.lookup_prefixes:
            search_field = search_field[1:]
        return search_field.split(LOOKUP_SEP)[0]


class QLSearch(SearchFilter):
    """rest_framework search filter which uses DjangoQL"""

    def __init__(self):
        super().__init__()
        self._fallback = HiddenFieldsSearchFilter()

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
        rules = EndpointChecks.for_request(request).field_rules()
        rules.refuse_hidden_parameters(request, view)
        self._fallback.hidden_whole_fields = rules.hidden_whole_fields
        search_query = self.get_search_terms(request)
        schema = self.get_schema(request, view)
        if len(search_query) == 0:
            return self._fallback.filter_queryset(request, queryset, view)
        try:
            return self.apply_search(queryset, search_query, schema, rules)
        except DjangoQLError as exc:
            LOGGER.debug("Failed to parse search expression", exc=exc)
            return self._fallback.filter_queryset(request, queryset, view)

    def apply_search(
        self, queryset: QuerySet, search: str, schema: type[BaseSchema], rules: FieldRules
    ) -> QuerySet:
        """This is a rewrite of `djangoql.queryset.apply_search`"""
        ast = DjangoQLParser().parse(search)
        if rules.hidden:
            rules.guard_search(ast)
        schema_instance = schema(queryset.model)
        schema_instance.validate(ast)
        return queryset.filter(build_filter(ast, schema_instance))
