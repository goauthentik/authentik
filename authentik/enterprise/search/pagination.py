from rest_framework.response import Response

from authentik.api.pagination import Pagination
from authentik.enterprise.search.ql import AUTOCOMPLETE_SCHEMA, QLSearch


class AutocompletePagination(Pagination):

    def paginate_queryset(self, queryset, request, view=None):
        self.view = view
        return super().paginate_queryset(queryset, request, view)

    def get_autocomplete(self):
        schema = QLSearch().get_schema(self.request, self.view)
        introspections = {}
        if hasattr(self.view, "get_ql_fields"):
            from authentik.enterprise.search.schema import AKQLSchemaSerializer

            introspections = AKQLSchemaSerializer().serialize(
                schema(self.page.paginator.object_list.model)
            )
        return introspections

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
                "autocomplete": self.get_autocomplete(),
            }
        )

    def get_paginated_response_schema(self, schema):
        final_schema = super().get_paginated_response_schema(schema)
        final_schema["properties"]["autocomplete"] = AUTOCOMPLETE_SCHEMA.ref
        final_schema["required"].append("autocomplete")
        return final_schema
