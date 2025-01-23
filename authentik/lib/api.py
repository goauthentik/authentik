from collections.abc import Callable, Sequence
from typing import Self
from uuid import UUID

from django.db.models import Model, Q, QuerySet, UUIDField
from django.shortcuts import get_object_or_404


class MultipleFieldLookupMixin:
    """Helper mixin class to add support for multiple lookup_fields.
    `lookup_fields` needs to be set which specifies the actual fields to query, `lookup_field`
    is only used to generate the URL."""

    lookup_field: str
    lookup_fields: str | Sequence[str]

    get_queryset: Callable[[Self], QuerySet]
    filter_queryset: Callable[[Self, QuerySet], QuerySet]

    def get_object(self):
        queryset: QuerySet = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        if isinstance(self.lookup_fields, str):
            self.lookup_fields = [self.lookup_fields]
        query = Q()
        model: Model = queryset.model
        for field in self.lookup_fields:
            field_inst = model._meta.get_field(field)
            # Sanity check, if the field we're filtering again, only apply the filter if
            # our value looks like a UUID
            if isinstance(field_inst, UUIDField):
                try:
                    UUID(self.kwargs[self.lookup_field])
                except ValueError:
                    continue
            query |= Q(**{field: self.kwargs[self.lookup_field]})
        return get_object_or_404(queryset, query)
