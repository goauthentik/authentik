"""authentik database utilities"""

import gc
from collections.abc import Generator

from django.core.exceptions import EmptyResultSet
from django.db import connections, reset_queries, transaction
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


def distinct_values(queryset: QuerySet, field: str) -> list:
    """Return the distinct non-null values of `field` in `queryset` as the database returns
    them, in ascending order.

    `SELECT DISTINCT` reads every row. When `field` is indexed and has few distinct values,
    stepping from each value to the next through the index reads one index entry per value
    instead, which is far cheaper on large tables such as events. This is the recursive query
    from https://wiki.postgresql.org/wiki/Loose_indexscan, with the queryset's filters applied
    at each step. Those filters may only use the queryset's own table."""
    if len(queryset.query.alias_map) > 1:
        raise ValueError("distinct_values cannot filter through a join")
    db = connections[queryset.db]
    table = db.ops.quote_name(queryset.model._meta.db_table)
    column = f"{table}.{db.ops.quote_name(queryset.model._meta.get_field(field).column)}"
    try:
        where, params = queryset.query.get_compiler(using=queryset.db).compile(queryset.query.where)
    except EmptyResultSet:
        return []
    where = f"AND {where}" if where else ""
    with db.cursor() as cursor:
        cursor.execute(
            f"""
            WITH RECURSIVE distinct_values(value) AS (
                SELECT MIN({column}) FROM {table} WHERE TRUE {where}
                UNION ALL
                SELECT (
                    SELECT MIN({column}) FROM {table}
                    WHERE {column} > distinct_values.value {where}
                )
                FROM distinct_values WHERE value IS NOT NULL
            )
            SELECT value FROM distinct_values WHERE value IS NOT NULL
            """,  # nosec: identifiers come from the model and values are in params
            (*params, *params),
        )
        return [value for (value,) in cursor.fetchall()]
