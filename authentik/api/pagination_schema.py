"""Swagger Pagination Schema class"""
from typing import OrderedDict

from drf_yasg2 import openapi
from drf_yasg2.inspectors import PaginatorInspector


class PaginationInspector(PaginatorInspector):
    """Swagger Pagination Schema class"""

    def get_paginated_response(self, paginator, response_schema):
        """
        :param BasePagination paginator: the paginator
        :param openapi.Schema response_schema: the response schema that must be paged.
        :rtype: openapi.Schema
        """

        return openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties=OrderedDict(
                (
                    (
                        "pagination",
                        openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties=OrderedDict(
                                (
                                    ("next", openapi.Schema(type=openapi.TYPE_NUMBER)),
                                    (
                                        "previous",
                                        openapi.Schema(type=openapi.TYPE_NUMBER),
                                    ),
                                    ("count", openapi.Schema(type=openapi.TYPE_NUMBER)),
                                    (
                                        "current",
                                        openapi.Schema(type=openapi.TYPE_NUMBER),
                                    ),
                                    (
                                        "total_pages",
                                        openapi.Schema(type=openapi.TYPE_NUMBER),
                                    ),
                                    (
                                        "start_index",
                                        openapi.Schema(type=openapi.TYPE_NUMBER),
                                    ),
                                    (
                                        "end_index",
                                        openapi.Schema(type=openapi.TYPE_NUMBER),
                                    ),
                                )
                            ),
                        ),
                    ),
                    ("results", response_schema),
                )
            ),
            required=["results", "pagination"],
        )

    def get_paginator_parameters(self, paginator):
        """
        Get the pagination parameters for a single paginator **instance**.

        Should return :data:`.NotHandled` if this inspector
        does not know how to handle the given `paginator`.

        :param BasePagination paginator: the paginator
        :rtype: list[openapi.Parameter]
        """

        return [
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                "Page Index",
                False,
                None,
                openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                "Page Size",
                False,
                None,
                openapi.TYPE_INTEGER,
            ),
        ]
