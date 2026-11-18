"""authentik database utilities"""

import gc
from collections.abc import Generator

from django.db import reset_queries, transaction
from django.db.models import Model, QuerySet


def chunked_queryset[T: Model](queryset: QuerySet[T], chunk_size: int = 1_000) -> Generator[T]:
    if not queryset.exists():
        return

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


def delete_in_batches[T: Model](queryset: QuerySet[T], batch_size: int = 1_000) -> int:
    """Delete matching rows in short transactions, returning the target model's count.

    Call outside an enclosing transaction to release locks after each batch. Use only
    for models that do not require instance-level delete/expiration hooks; Django's
    deletion signals and cascades still run. Rows locked by another transaction are
    skipped and may need a later cleanup run.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    # SELECT FOR UPDATE also selects the write database when routers are configured.
    queryset = queryset.select_for_update(skip_locked=True, of=("self",))
    database = queryset.db
    queryset = queryset.using(database)
    deleted_total = 0
    while True:
        with transaction.atomic(using=database):
            pks = list(queryset.order_by("pk").values_list("pk", flat=True)[:batch_size])
            if not pks:
                return deleted_total
            # Hold the locks through Django's collector and DELETE so that a cache
            # refresh cannot race with deletion after the expiration check.
            _, counts = queryset.filter(pk__in=pks).delete()
            deleted_total += counts.get(queryset.model._meta.label, 0)
