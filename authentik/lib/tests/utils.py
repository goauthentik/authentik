"""Test utils"""

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from inspect import currentframe
from pathlib import Path

from django.db import connection
from django.db.models import Model


def load_fixture(path: str, path_only=False, **kwargs) -> str:
    """Load fixture, optionally formatting it with kwargs"""
    current = currentframe()
    parent = current.f_back
    calling_file_path = parent.f_globals["__file__"]
    fixture_path = Path(calling_file_path).resolve().parent / Path(path)
    if path_only:
        return fixture_path
    with open(fixture_path, encoding="utf-8") as _fixture:
        fixture = _fixture.read()
        try:
            return fixture % kwargs
        except TypeError, ValueError:
            return fixture


@dataclass
class RowCounts:
    """Rows read from and deleted in one table"""

    read: int = 0
    deleted: int = 0


def _table_counts(model: type[Model]) -> tuple[int, int]:
    with connection.cursor() as cursor:
        # Make rows read by already committed transactions visible, see
        # https://www.postgresql.org/docs/current/monitoring-stats.html
        cursor.execute("SELECT pg_stat_force_next_flush()")
        cursor.execute("SELECT pg_stat_clear_snapshot()")
        cursor.execute(
            "SELECT t.seq_tup_read + coalesce(t.idx_tup_fetch, 0) "
            "+ x.seq_tup_read + coalesce(x.idx_tup_fetch, 0), t.n_tup_del + x.n_tup_del "
            "FROM pg_stat_user_tables t JOIN pg_stat_xact_user_tables x USING (relid) "
            "WHERE relid = %s::regclass",
            [model._meta.db_table],
        )
        return cursor.fetchone()


@contextmanager
def count_rows(model: type[Model]) -> Generator[RowCounts]:
    """Count the rows the enclosed code reads from and deletes in `model`'s table.

    Unlike timing, this gives the same result on every machine, so tests can bound rows read
    per row deleted to catch queries that scan the whole table instead of an index range.

    Postgres plans small test tables differently from large production ones: a sequential
    scan is cheapest when everything fits in a few pages. Sequential and bitmap scans are
    disabled while counting, so queries get the index plans they would get at scale."""
    with connection.cursor() as cursor:
        cursor.execute(f"ANALYZE {model._meta.db_table}")
    counts = RowCounts()
    read, deleted = _table_counts(model)
    with connection.cursor() as cursor:
        cursor.execute("SET enable_seqscan = off")
        cursor.execute("SET enable_bitmapscan = off")
    try:
        yield counts
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET enable_seqscan")
            cursor.execute("RESET enable_bitmapscan")
    after_read, after_deleted = _table_counts(model)
    counts.read, counts.deleted = after_read - read, after_deleted - deleted
