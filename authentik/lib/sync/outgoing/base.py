"""Basic outgoing sync Client"""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import timedelta
from enum import StrEnum
from typing import TYPE_CHECKING

import pglock
from deepmerge import always_merger
from django.db import DatabaseError, connection
from structlog.stdlib import get_logger

from authentik.core.expression.exceptions import (
    PropertyMappingExpressionException,
)
from authentik.events.models import Event, EventAction
from authentik.lib.config import advisory_lock_db_alias
from authentik.lib.expression.exceptions import ControlFlowException
from authentik.lib.sync.mapper import PropertyMappingManager
from authentik.lib.sync.outgoing.exceptions import (
    NotFoundSyncException,
    ObjectLockTimeout,
    StopSync,
)

if TYPE_CHECKING:
    from django.db.models import Model

    from authentik.lib.sync.outgoing.models import OutgoingSyncProvider


class Direction(StrEnum):
    add = "add"
    remove = "remove"


SAFE_METHODS = [
    "GET",
    "HEAD",
    "OPTIONS",
    "TRACE",
]

OBJECT_LOCK_TIMEOUT = timedelta(seconds=30)


class BaseOutgoingSyncClient[
    TModel: "Model",
    TConnection: "Model",
    TSchema: dict,
    TProvider: "OutgoingSyncProvider",
]:
    """Basic Outgoing sync client Client"""

    provider: TProvider
    connection_type: type[TConnection]
    connection_type_query: str
    mapper: PropertyMappingManager

    can_discover = False

    def __init__(self, provider: TProvider):
        self.logger = get_logger().bind(provider=provider.name)
        self.provider = provider

    def create(self, obj: TModel) -> TConnection:
        """Create object in remote destination"""
        raise NotImplementedError()

    def update(self, obj: TModel, connection: TConnection):
        """Update object in remote destination"""
        raise NotImplementedError()

    @contextmanager
    def object_lock(self, obj: TModel) -> Iterator[None]:
        """Serialize remote operations for one object and provider."""
        lock_id = (
            f"goauthentik.io/{connection.schema_name}/providers/outgoing-sync/"
            f"{self.provider._meta.label_lower}/{self.provider.pk}/"
            f"{obj._meta.label_lower}/{obj.pk}"
        )
        with pglock.advisory(
            lock_id=lock_id,
            timeout=OBJECT_LOCK_TIMEOUT,
            side_effect=pglock.Return,
            using=advisory_lock_db_alias(),
        ) as lock_acquired:
            if not lock_acquired:
                raise ObjectLockTimeout(lock_id)
            yield

    def write(self, obj: TModel) -> tuple[TConnection, bool]:
        """Write an object to the destination while holding its object lock."""
        with self.object_lock(obj):
            return self._write(obj)

    def _write(self, obj: TModel) -> tuple[TConnection, bool]:
        """Write an object while the caller holds its object lock."""
        connection = self.connection_type.objects.filter(
            provider=self.provider, **{self.connection_type_query: obj}
        ).first()
        try:
            if not connection:
                connection = self.create(obj)
                return connection, True
            try:
                self.update(obj, connection)
                return connection, False
            except NotFoundSyncException:
                connection.delete()
                connection = self.create(obj)
                return connection, True
        except DatabaseError as exc:
            self.logger.warning("Failed to write object", obj=obj, exc=exc)
            if connection:
                connection.delete()
        return None, False

    def sync_group_membership(self, obj: TModel, action: Direction, users_set: set[int]) -> None:
        """Update group membership while holding the same lock used by writes."""
        with self.object_lock(obj):
            self.update_group(obj, action, users_set)

    def update_group(self, obj: TModel, action: Direction, users_set: set[int]) -> None:
        """Update group membership in the remote destination."""
        raise NotImplementedError()

    def delete(self, identifier: str):
        """Delete object from destination"""
        raise NotImplementedError()

    def to_schema(self, obj: TModel, connection: TConnection | None, **defaults) -> TSchema:
        """Convert object to destination schema"""
        raw_final_object = {}
        try:
            eval_kwargs = {
                "request": None,
                "provider": self.provider,
                "connection": connection,
                obj._meta.model_name: obj,
            }
            eval_kwargs.setdefault("user", None)
            for value in self.mapper.iter_eval(**eval_kwargs):
                always_merger.merge(raw_final_object, value)
        except ControlFlowException as exc:
            raise exc from exc
        except PropertyMappingExpressionException as exc:
            # Value error can be raised when assigning invalid data to an attribute
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message="Failed to evaluate property-mapping",
                mapping=exc.mapping,
            ).with_exception(exc).save()
            raise StopSync(exc, obj, exc.mapping) from exc
        if not raw_final_object:
            raise StopSync(ValueError("No mappings configured"), obj)
        for key, value in defaults.items():
            raw_final_object.setdefault(key, value)
        return raw_final_object

    def discover(self):
        """Optional method. Can be used to implement a "discovery" where
        upon creation of this provider, this function will be called and can
        pre-link any users/groups in the remote system with the respective
        object in authentik based on a common identifier"""
        raise NotImplementedError()

    def update_single_attribute(self, connection: TConnection):
        """Update connection attributes on a connection object, when the connection
        is manually created"""
        raise NotImplementedError
