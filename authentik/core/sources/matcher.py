"""Source user and group matching"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from django.db.models import Q
from structlog import get_logger

from authentik.core.models import (
    Group,
    GroupSourceConnection,
    Source,
    SourceGroupMatchingModes,
    SourceUserMatchingModes,
    User,
    UserSourceConnection,
)


class Action(Enum):
    """Actions that can be decided based on the request and source settings"""

    LINK = "link"
    AUTH = "auth"
    ENROLL = "enroll"
    DENY = "deny"


@dataclass
class MatchableProperty:
    property: str
    link_mode: SourceUserMatchingModes | SourceGroupMatchingModes
    deny_mode: SourceUserMatchingModes | SourceGroupMatchingModes


class SourceMatcher:
    def __init__(
        self,
        source: Source,
        user_connection_type: type[UserSourceConnection],
        group_connection_type: type[GroupSourceConnection],
    ):
        self.source = source
        self.user_connection_type = user_connection_type
        self.group_connection_type = group_connection_type
        self._logger = get_logger().bind(source=self.source)

    def get_action(
        self,
        object_type: type[User | Group],
        matchable_properties: list[MatchableProperty],
        identifier: str,
        properties: dict[str, Any | dict[str, Any]],
    ) -> tuple[Action, UserSourceConnection | GroupSourceConnection | None]:
        connection_type = None
        matching_mode = None
        identifier_matching_mode = None
        if object_type == User:
            connection_type = self.user_connection_type
            matching_mode = self.source.user_matching_mode
            identifier_matching_mode = SourceUserMatchingModes.IDENTIFIER
        if object_type == Group:
            connection_type = self.group_connection_type
            matching_mode = self.source.group_matching_mode
            identifier_matching_mode = SourceGroupMatchingModes.IDENTIFIER
        if not connection_type or not matching_mode or not identifier_matching_mode:
            return Action.DENY, None

        new_connection = connection_type(source=self.source, identifier=identifier)

        existing_connections = connection_type.objects.filter(
            source=self.source, identifier=identifier
        )
        if existing_connections.exists():
            return Action.AUTH, existing_connections.first()
        # No connection exists, but we match on identifier, so enroll
        if matching_mode == identifier_matching_mode:
            # We don't save the connection here cause it doesn't have a user/group assigned yet
            return Action.ENROLL, new_connection

        # Check for existing users with matching attributes
        query = Q()
        for matchable_property in matchable_properties:
            property = matchable_property.property
            if matching_mode in [matchable_property.link_mode, matchable_property.deny_mode]:
                if not properties.get(property, None):
                    self._logger.warning(
                        "Refusing to use none property", identifier=identifier, property=property
                    )
                    return Action.DENY, None
                query_args = {
                    f"{property}__exact": properties[property],
                }
                query = Q(**query_args)
        self._logger.debug(
            "Trying to link with existing object", query=query, identifier=identifier
        )
        matching_objects = object_type.objects.filter(query)
        # Not matching objects, always enroll
        if not matching_objects.exists():
            self._logger.debug("No matching objects found, enrolling")
            return Action.ENROLL, new_connection

        obj = matching_objects.first()
        if matching_mode in [mp.link_mode for mp in matchable_properties]:
            attr = None
            if object_type == User:
                attr = "user"
            if object_type == Group:
                attr = "group"
            setattr(new_connection, attr, obj)
            return Action.LINK, new_connection
        if matching_mode in [mp.deny_mode for mp in matchable_properties]:
            self._logger.info("Denying source because object exists", obj=obj)
            return Action.DENY, None

        # Should never get here as default enroll case is returned above.
        return Action.DENY, None  # pragma: no cover

    def get_user_action(
        self, identifier: str, properties: dict[str, Any | dict[str, Any]]
    ) -> tuple[Action, UserSourceConnection | None]:
        return self.get_action(
            User,
            [
                MatchableProperty(
                    "username",
                    SourceUserMatchingModes.USERNAME_LINK,
                    SourceUserMatchingModes.USERNAME_DENY,
                ),
                MatchableProperty(
                    "email", SourceUserMatchingModes.EMAIL_LINK, SourceUserMatchingModes.EMAIL_DENY
                ),
            ],
            identifier,
            properties,
        )

    def get_group_action(
        self, identifier: str, properties: dict[str, Any | dict[str, Any]]
    ) -> tuple[Action, GroupSourceConnection | None]:
        return self.get_action(
            Group,
            [
                MatchableProperty(
                    "name", SourceGroupMatchingModes.NAME_LINK, SourceGroupMatchingModes.NAME_DENY
                ),
            ],
            identifier,
            properties,
        )
