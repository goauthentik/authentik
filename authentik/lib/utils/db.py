"""authentik database utilities"""

import gc
from collections.abc import Generator
from typing import TypeVar

from django.db import reset_queries
from django.db.models import Model, QuerySet

ModelT_co = TypeVar("ModelT_co", bound=Model, covariant=True)


def chunked_queryset(
    queryset: QuerySet[ModelT_co], chunk_size: int = 1_000
) -> Generator[ModelT_co]:
    if not queryset.exists():
        return

    def get_chunks(qs: QuerySet[ModelT_co]) -> Generator[QuerySet[ModelT_co]]:
        qs = qs.order_by("pk")
        pks = qs.values_list("pk", flat=True)
        start_pk = pks[0]
        while True:
            try:
                end_pk = pks.filter(pk__gte=start_pk)[chunk_size]
            except IndexError:
                break
            yield qs.filter(pk__gte=start_pk, pk__lt=end_pk)
            start_pk = end_pk
        yield qs.filter(pk__gte=start_pk)

    for chunk in get_chunks(queryset):
        reset_queries()
        gc.collect()
        yield from chunk.iterator()
