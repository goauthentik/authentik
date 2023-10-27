"""Pagination which includes total pages and current page"""
from rest_framework import pagination
from rest_framework.response import Response

PAGINATION_COMPONENT_NAME = "Pagination"
PAGINATION_SCHEMA = {
    "type": "object",
    "properties": {
        "next": {
            "type": "number",
        },
        "previous": {
            "type": "number",
        },
        "count": {
            "type": "number",
        },
        "current": {
            "type": "number",
        },
        "total_pages": {
            "type": "number",
        },
        "start_index": {
            "type": "number",
        },
        "end_index": {
            "type": "number",
        },
    },
    "required": [
        "next",
        "previous",
        "count",
        "current",
        "total_pages",
        "start_index",
        "end_index",
    ],
}


class Pagination(pagination.PageNumberPagination):
    """Pagination which includes total pages and current page"""

    page_query_param = "page"
    page_size_query_param = "page_size"

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
        return {
            "type": "object",
            "properties": {
                "pagination": {"$ref": f"#/components/schemas/{PAGINATION_COMPONENT_NAME}"},
                "results": schema,
            },
            "required": ["pagination", "results"],
        }


class SmallerPagination(Pagination):
    """Smaller pagination for objects which might require a lot of queries
    to retrieve all data for."""

    max_page_size = 10
