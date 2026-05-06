from django.db.models import F
from rest_framework.filters import OrderingFilter


class NullsAwareOrderingFilter(OrderingFilter):
    """OrderingFilter that sorts NULL values consistently.

    For any nullable field, NULLs are treated as the smallest possible value:
    - ascending  → NULLs appear first  (nulls_first=True)
    - descending → NULLs appear last   (nulls_last=True)
    """

    def _nullable_field_names(self, queryset) -> set[str]:
        return {f.name for f in queryset.model._meta.get_fields() if hasattr(f, "null") and f.null}

    def filter_queryset(self, request, queryset, view):
        queryset = super().filter_queryset(request, queryset, view)
        ordering = queryset.query.order_by
        if not ordering:
            return queryset
        nullable = self._nullable_field_names(queryset)
        new_ordering = []
        changed = False
        for term in ordering:
            name = term.lstrip("-")
            if name in nullable:
                changed = True
                if term.startswith("-"):
                    new_ordering.append(F(name).desc(nulls_last=True))
                else:
                    new_ordering.append(F(name).asc(nulls_first=True))
            else:
                new_ordering.append(term)
        return queryset.order_by(*new_ordering) if changed else queryset
