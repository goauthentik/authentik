"""Pagination which includes total pages and current page"""

from drf_spectacular.plumbing import build_object_type
from rest_framework import pagination
from rest_framework.response import Response

from authentik.api.v3.schema.response import PAGINATION
from authentik.lib.config import CONFIG


class Pagination(pagination.PageNumberPagination):
    """Pagination which includes total pages and current page"""

    page_query_param = "page"
    page_size_query_param = "page_size"
    max_page_size = CONFIG.get("pagination.max_page_size")

    def get_paginated_response(self, data):
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
            }
        )

    def get_paginated_response_schema(self, schema):
        return build_object_type(
            properties={
                "pagination": PAGINATION.ref,
                "results": schema,
            },
            required=["pagination", "results"],
        )


class SmallerPagination(Pagination):
    """Smaller pagination for objects which might require a lot of queries
    to retrieve all data for."""

    max_page_size = 10
