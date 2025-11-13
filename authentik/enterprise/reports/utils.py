import csv
import io
from collections.abc import Iterable
from dataclasses import dataclass

from django.core.files.base import File

from authentik.core.models import User
from authentik.tenants.models import Tenant


@dataclass
class MockRequest:
    user: User
    query_params: dict[str, str]
    tenant: Tenant


class ChunkedCSVOutputFile(File):
    """
    File-like object that yields CSV data in chunks from an iterable of rows.
    """

    def __init__(self, rows: Iterable, name: str = None):
        super().__init__(None, name=name)
        self.rows = rows

    def multiple_chunks(self, chunk_size: int | None = None) -> bool | None:
        return True

    def chunks(self, chunk_size: int | None = None) -> Iterable[bytes]:
        csize = chunk_size or self.DEFAULT_CHUNK_SIZE
        with io.TextIOWrapper(io.BytesIO(), encoding="utf-8") as chunk:
            writer = csv.writer(chunk)
            it = iter(self.rows)
            done = False
            while not done:
                while chunk.tell() < csize:
                    try:
                        row = next(it)
                    except StopIteration:
                        done = True
                        break
                    writer.writerow(row)
                if chunk.tell() == 0:
                    break
                chunk.seek(0)
                yield chunk.read()
                chunk.truncate(0)
                chunk.seek(0)
