"""Sync Kerberos users into authentik"""

from typing import Any

from django.core.exceptions import FieldError
from django.db import IntegrityError, transaction
from kadmin import KAdmin
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.expression.exceptions import (
    PropertyMappingExpressionException,
    SkipObjectException,
)
from authentik.core.models import Group, User, UserTypes
from authentik.core.sources.mapper import SourceMapper
from authentik.core.sources.matcher import Action, SourceMatcher
from authentik.events.models import Event, EventAction
from authentik.lib.sync.mapper import PropertyMappingManager
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.sources.kerberos.models import (
    GroupKerberosSourceConnection,
    KerberosSource,
    Krb5ConfContext,
    UserKerberosSourceConnection,
)
from authentik.tasks.models import Task


class KerberosSync:
    """Sync Kerberos users into authentik"""

    _source: KerberosSource
    _task: Task
    _logger: BoundLogger
    _connection: KAdmin
    mapper: SourceMapper
    user_manager: PropertyMappingManager
    group_manager: PropertyMappingManager
    matcher: SourceMatcher

    def __init__(self, source: KerberosSource, task: Task):
        self._source = source
        self._task = task
        with Krb5ConfContext(self._source):
            self._connection = self._source.connection()
        self._logger = get_logger().bind(source=self._source, syncer=self.__class__.__name__)
        self.mapper = SourceMapper(self._source)
        self.user_manager = self.mapper.get_manager(User, ["principal", "principal_obj"])
        self.group_manager = self.mapper.get_manager(
            Group, ["group_id", "principal", "principal_obj"]
        )
        self.matcher = SourceMatcher(
            self._source, UserKerberosSourceConnection, GroupKerberosSourceConnection
        )

    @staticmethod
    def name() -> str:
        """UI name for the type of object this class synchronizes"""
        return "users"

    def _handle_principal(self, principal: str) -> bool:
        try:
            # TODO: handle permission error
            principal_obj = self._connection.get_principal(principal)

            defaults = self.mapper.build_object_properties(
                object_type=User,
                manager=self.user_manager,
                user=None,
                request=None,
                principal=principal,
                principal_obj=principal_obj,
            )
            self._logger.debug("Writing user with attributes", **defaults)
            if "username" not in defaults:
                raise IntegrityError("Username was not set by propertymappings")

            action, connection = self.matcher.get_user_action(principal, defaults)
            self._logger.debug("Action returned", action=action, connection=connection)
            if action == Action.DENY:
                return False

            group_properties = {
                group_id: self.mapper.build_object_properties(
                    object_type=Group,
                    manager=self.group_manager,
                    user=None,
                    request=None,
                    group_id=group_id,
                    principal=principal,
                    principal_obj=principal_obj,
                )
                for group_id in defaults.pop("groups", [])
            }

            if action == Action.ENROLL:
                user = User.objects.create(**defaults)
                if user.type == UserTypes.INTERNAL_SERVICE_ACCOUNT:
                    user.set_unusable_password()
                    user.save()
                connection.user = user
                connection.save()
            elif action in (Action.AUTH, Action.LINK):
                user = connection.user
                user.update_attributes(defaults)
            else:
                return False

            groups: list[Group] = []
            for group_id, properties in group_properties.items():
                group = self._handle_group(group_id, properties)
                if group:
                    groups.append(group)

            with transaction.atomic():
                user.ak_groups.remove(
                    *user.ak_groups.filter(groupsourceconnection__source=self._source)
                )
                user.ak_groups.add(*groups)

        except PropertyMappingExpressionException as exc:
            raise StopSync(exc, None, exc.mapping) from exc
        except SkipObjectException:
            return False
        except (IntegrityError, FieldError, TypeError, AttributeError) as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=(f"Failed to create user: {str(exc)} "),
                source=self._source,
                principal=principal,
            ).save()
            return False
        self._logger.debug("Synced User", user=user.username)
        return True

    def _handle_group(
        self, group_id: str, defaults: dict[str, Any | dict[str, Any]]
    ) -> Group | None:
        action, connection = self.matcher.get_group_action(group_id, defaults)
        if action == Action.DENY:
            return None
        if action == Action.ENROLL:
            group = Group.objects.create(**defaults)
            connection.group = group
            connection.save()
            return group
        if action in (Action.AUTH, Action.LINK):
            group = connection.group
            group.update_attributes(defaults)
            connection.save()
            return group
        return None

    def sync(self) -> int:
        """Iterate over all Kerberos users and create authentik_core.User instances"""
        if not self._source.enabled or not self._source.sync_users:
            self._task.info("Source is disabled or user syncing is disabled for this Source")
            return -1

        user_count = 0
        with Krb5ConfContext(self._source):
            for principal in self._connection.list_principals(None):
                if self._handle_principal(principal):
                    user_count += 1
        return user_count
