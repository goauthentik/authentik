"""authentik database utilities"""

import gc
from collections.abc import Generator

from django.db import reset_queries
from django.db.models import Model, QuerySet


def chunked_queryset[T: Model](queryset: QuerySet[T], chunk_size: int = 1_000) -> Generator[T]:
    if not queryset.exists():
        return []

    def get_chunks(qs: QuerySet) -> Generator[QuerySet[T]]:
        qs = qs.order_by("pk")
        pks = qs.values_list("pk", flat=True)
        # The outer queryset.exists() guard can race with a concurrent
        # transaction that deletes the last matching row (or with a
        # different isolation-level snapshot), so by the time this
        # generator starts iterating the queryset may be empty and
        # pks[0] would raise IndexError and crash the caller. Using
        # .first() returns None on an empty queryset, which we bail
        # out on cleanly. See goauthentik/authentik#21643.
        start_pk = pks.first()
        if start_pk is None:
            return
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
        yield from chunk.iterator(chunk_size=chunk_size)
