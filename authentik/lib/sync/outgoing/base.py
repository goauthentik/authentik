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

    can_discover = False

    def __init__(self, provider: TProvider):
        self.logger = get_logger().bind(provider=provider.name)
        self.provider = provider

    def create(self, obj: TModel) -> TConnection:
        """Create object in remote destination"""
        raise NotImplementedError()

    def update(self, obj: TModel, connection: object):
        """Update object in remote destination"""
        raise NotImplementedError()

    def write(self, obj: TModel) -> tuple[TConnection, bool]:
        """Write object to destination. Uses self.create and self.update, but
        can be overwritten for further logic"""
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

    def discover(self):
        """Optional method. Can be used to implement a "discovery" where
        upon creation of this provider, this function will be called and can
        pre-link any users/groups in the remote system with the respective
        object in authentik based on a common identifier"""
        raise NotImplementedError()
