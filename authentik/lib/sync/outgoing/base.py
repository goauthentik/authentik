"""Basic outgoing sync Client"""

from enum import StrEnum
from typing import TYPE_CHECKING

from django.db import DatabaseError
from structlog.stdlib import get_logger

from authentik.lib.sync.outgoing.exceptions import NotFoundSyncException

if TYPE_CHECKING:
    from django.db.models import Model

    from authentik.lib.sync.outgoing.models import OutgoingSyncProvider


class Direction(StrEnum):

    add = "add"
    remove = "remove"


class BaseOutgoingSyncClient[
    TModel: "Model", TConnection: "Model", TSchema: dict, TProvider: "OutgoingSyncProvider"
]:
    """Basic Outgoing sync client Client"""

    provider: TProvider
    connection_type: type[TConnection]
    connection_type_query: str

    def __init__(self, provider: TProvider):
        self.logger = get_logger().bind(provider=provider.name)
        self.provider = provider

    def create(self, obj: TModel) -> TConnection:
        raise NotImplementedError()

    def update(self, obj: TModel, connection: object):
        raise NotImplementedError()

    def write(self, obj: TModel) -> tuple[TConnection, bool]:
        """Write object to destination"""
        remote_obj = self.connection_type.objects.filter(
            provider=self.provider, **{self.connection_type_query: obj}
        ).first()
        connection: TConnection | None = None
        try:
            if not remote_obj:
                connection = self.create(obj)
                return connection, True
            try:
                self.update(obj, remote_obj)
                return remote_obj, False
            except NotFoundSyncException:
                remote_obj.delete()
                connection = self.create(obj)
                return connection, True
        except DatabaseError as exc:
            self.logger.warning("Failed to write object", obj=obj, exc=exc)
            if connection:
                connection.delete()
        return None, False

    def delete(self, obj: TModel):
        """Delete object from destination"""
        raise NotImplementedError()

    def to_schema(self, obj: TModel) -> TSchema:
        """Convert object to destination schema"""
        raise NotImplementedError()
