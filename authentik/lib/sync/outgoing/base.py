"""Basic outgoing sync Client"""

from enum import StrEnum
from typing import TYPE_CHECKING

from structlog.stdlib import get_logger

if TYPE_CHECKING:
    from django.db.models import Model

    from authentik.lib.sync.outgoing.models import OutgoingSyncProvider


class Direction(StrEnum):

    add = "add"
    remove = "remove"


class BaseOutgoingSyncClient[TModel: "Model", TSchema: dict, TProvider: "OutgoingSyncProvider"]:
    """Basic Outgoing sync client Client"""

    provider: TProvider

    def __init__(self, provider: TProvider):
        self.logger = get_logger().bind(provider=provider.name)

    def write(self, obj: TModel):
        """Write object to destination"""
        raise NotImplementedError()

    def delete(self, obj: TModel):
        """Delete object from destination"""
        raise NotImplementedError()

    def to_schema(self, obj: TModel) -> TSchema:
        """Convert object to destination schema"""
        raise NotImplementedError()
