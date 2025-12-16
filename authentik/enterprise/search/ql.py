"""QL search"""

from akql.exceptions import AKQLError
from akql.queryset import apply_search
from akql.schema import AKQLSchema
from django.apps import apps
from django.db.models import QuerySet
from drf_spectacular.plumbing import ResolvedComponent, build_object_type
from rest_framework.filters import SearchFilter
from rest_framework.request import Request
from structlog.stdlib import get_logger

LOGGER = get_logger()
AUTOCOMPLETE_SCHEMA = ResolvedComponent(
    name="Autocomplete",
    object="Autocomplete",
    type=ResolvedComponent.SCHEMA,
    schema=build_object_type(additionalProperties={}),
)


class QLSearch(SearchFilter):
    """rest_framework search filter which uses AKQL"""

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

    def get_schema(self, request: Request, view) -> AKQLSchema:
        ql_fields = []
        if hasattr(view, "get_ql_fields"):
            ql_fields = view.get_ql_fields()

        class InlineSchema(AKQLSchema):
            def get_fields(self, model):
                return ql_fields or []

        return InlineSchema

    def get_search_context(self, request: Request):
        return {
            "$ak_user": request.user.pk,
        }

    def filter_queryset(self, request: Request, queryset: QuerySet, view) -> QuerySet:
        search_query = self.get_search_terms(request)
        schema = self.get_schema(request, view)
        if len(search_query) == 0 or not self.enabled:
            return self._fallback.filter_queryset(request, queryset, view)
        context = self.get_search_context(request)
        try:
            return apply_search(queryset, search_query, context=context, schema=schema)
        except AKQLError as exc:
            LOGGER.debug("Failed to parse search expression", exc=exc)
            return self._fallback.filter_queryset(request, queryset, view)
