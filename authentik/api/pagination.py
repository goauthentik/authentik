"""Pagination which includes total pages and current page"""

from typing import TYPE_CHECKING

from drf_spectacular.plumbing import build_object_type
from rest_framework import pagination
from rest_framework.response import Response

from authentik.api.search.ql import QLSearch
from authentik.api.v3.schema.pagination import PAGINATION
from authentik.api.v3.schema.search import AUTOCOMPLETE_SCHEMA

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from rest_framework.request import Request


class Pagination(pagination.PageNumberPagination):
    """Pagination which includes total pages and current page"""

    page_query_param = "page"
    page_size_query_param = "page_size"

    def get_page_size(self, request: Request) -> int:
        if self.page_size_query_param in request.query_params:
            page_size = super().get_page_size(request)
            if page_size is not None:
                return min(super().get_page_size(request), request.tenant.pagination_max_page_size)
        return request.tenant.pagination_default_page_size

    def get_paginated_response(self, data) -> Response:
        previous_page_number = 0
        if self.page.has_previous():
            previous_page_number = self.page.previous_page_number()
        next_page_number = 0
        if self.page.has_next():
            next_page_number = self.page.next_page_number()
        return Response(
            {
                "pagination": {
                    "next": next_page_number,
                    "previous": previous_page_number,
                    "count": self.page.paginator.count,
                    "current": self.page.number,
                    "total_pages": self.page.paginator.num_pages,
                    "start_index": self.page.start_index(),
                    "end_index": self.page.end_index(),
                },
                "results": data,
                "autocomplete": self.get_autocomplete(),
            }
        )

    def paginate_queryset(self, queryset: QuerySet, request: Request, view=None):
        self.view = view
        return super().paginate_queryset(queryset, request, view)

    def get_autocomplete(self):
        schema = QLSearch().get_schema(self.request, self.view)
        introspections = {}
        if hasattr(self.view, "get_ql_fields"):
            from authentik.api.search.schema import AKQLSchemaSerializer

            introspections = AKQLSchemaSerializer().serialize(
                schema(self.page.paginator.object_list.model)
            )
        return introspections

    def get_paginated_response_schema(self, schema):
        return build_object_type(
            properties={
                "pagination": PAGINATION.ref,
                "results": schema,
                "autocomplete": AUTOCOMPLETE_SCHEMA.ref,
            },
            required=["pagination", "results", "autocomplete"],
        )


class SmallerPagination(Pagination):
    """Smaller pagination for objects which might require a lot of queries
    to retrieve all data for."""

    max_page_size = 10
