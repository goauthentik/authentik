"""authentik database utilities"""

import gc

from django.db.models import QuerySet


def qs_batch_iter(qs: QuerySet, batch_size: int = 10_000, gc_collect: bool = True):
    pk_iter = qs.values_list("pk", flat=True).order_by("pk").distinct().iterator()
    eof = False
    while not eof:
        pk_buffer = []
        i = 0
        try:
            while i < batch_size:
                pk_buffer.append(pk_iter.next())
                i += 1
        except StopIteration:
            eof = True
        yield from qs.filter(pk__in=pk_buffer).order_by("pk").iterator()
        if gc_collect:
            gc.collect()
