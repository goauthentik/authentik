"""authentik database utilities"""

import gc
from collections.abc import Generator

from django.db import IntegrityError, reset_queries, transaction
from django.db.models import Model, ProtectedError, QuerySet, RestrictedError
from structlog.stdlib import get_logger

LOGGER = get_logger()


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

    Django collects the rows that reference a batch before it deletes the batch. A row
    that starts referencing the batch in between is not part of that collection, and the
    deferred foreign key check then fails the whole transaction on commit. Such a batch is
    retried in halves, so that the rows which can be deleted are, and only the rows that are
    actively being referenced are left for a later cleanup run. Inside an enclosing
    transaction that check only happens when the enclosing transaction is committed.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    # SELECT FOR UPDATE also selects the write database when routers are configured.
    queryset = queryset.select_for_update(skip_locked=True, of=("self",))
    database = queryset.db
    queryset = queryset.using(database)
    deleted_total = 0
    # Primary keys that could not be deleted, left for a later cleanup run
    deferred: list = []
    while True:
        remaining = queryset.exclude(pk__in=deferred) if deferred else queryset
        pks: list = []
        try:
            with transaction.atomic(using=database):
                pks = list(remaining.order_by("pk").values_list("pk", flat=True)[:batch_size])
                if not pks:
                    break
                # Hold the locks through Django's collector and DELETE so that a cache
                # refresh cannot race with deletion after the expiration check.
                _, counts = queryset.filter(pk__in=pks).delete()
            deleted_total += counts.get(queryset.model._meta.label, 0)
        except ProtectedError, RestrictedError:
            # The rows are referenced on purpose, retrying does not change that
            raise
        except IntegrityError:
            deleted, failed = _delete_in_halves(queryset, pks)
            if failed and not deleted:
                # Not a single row of the batch can be deleted, this is not a concurrent
                # write but a persistent problem that retrying will not solve.
                raise
            deleted_total += deleted
            deferred.extend(failed)
    if deferred:
        LOGGER.warning(
            "Rows could not be deleted as they are still referenced, leaving for next cleanup",
            model=queryset.model._meta.label,
            amount=len(deferred),
        )
    return deleted_total


def _delete_in_halves[T: Model](queryset: QuerySet[T], pks: list) -> tuple[int, list]:
    """Retry the deletion of `pks` after it failed with an integrity error, splitting the
    rows in halves until the rows that cannot be deleted are isolated. A single row is
    attempted once more on its own.

    Returns the target model's count of deleted rows and the primary keys that failed."""
    deleted_total = 0
    failed: list = []
    middle = len(pks) // 2
    for part in (pks[:middle], pks[middle:]) if middle else (pks,):
        try:
            with transaction.atomic(using=queryset.db):
                # Lock and check the rows again, they may have been refreshed, deleted or
                # locked by another transaction since the failed attempt.
                locked = list(queryset.filter(pk__in=part).values_list("pk", flat=True))
                if not locked:
                    continue
                _, counts = queryset.filter(pk__in=locked).delete()
            deleted_total += counts.get(queryset.model._meta.label, 0)
        except ProtectedError, RestrictedError:
            raise
        except IntegrityError:
            if len(part) == 1:
                failed.extend(part)
                continue
            deleted, part_failed = _delete_in_halves(queryset, part)
            deleted_total += deleted
            failed.extend(part_failed)
    return deleted_total, failed
