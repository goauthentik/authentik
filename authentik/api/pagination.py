"""Pagination which includes total pages and current page"""
from rest_framework import pagination
from rest_framework.response import Response


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
