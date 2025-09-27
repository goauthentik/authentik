"""authentik database utilities"""

from collections.abc import Iterator
import gc

from django.db import reset_queries
from django.db.models import Model, QuerySet


def chunked_queryset[M: Model](queryset: QuerySet[M], chunk_size: int = 1_000) -> Iterator[M]:
    if not queryset.exists():
        return

    def get_chunks(qs: QuerySet[M]) -> Iterator[QuerySet[M]]:
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
