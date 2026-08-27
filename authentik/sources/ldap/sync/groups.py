"""Sync LDAP Users and groups into authentik"""

from collections.abc import Generator

from django.core.exceptions import FieldError
from django.db.utils import IntegrityError
from ldap3 import ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, SUBTREE

from authentik.core.expression.exceptions import (
    PropertyMappingExpressionException,
    SkipObjectException,
)
from authentik.core.models import Group
from authentik.core.sources.mapper import SourceMapper
from authentik.core.sources.matcher import Action
from authentik.events.models import Event, EventAction
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.lib.utils.errors import exception_to_dict
from authentik.sources.ldap.models import (
    LDAP_UNIQUENESS,
    GroupLDAPSourceConnection,
    LDAPSource,
    flatten,
)
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer
from authentik.tasks.models import Task


class GroupLDAPSynchronizer(BaseLDAPSynchronizer):
    """Sync LDAP Users and groups into authentik"""

    def __init__(self, source: LDAPSource, task: Task):
        super().__init__(source, task)
        self._source = source
        self.mapper = SourceMapper(source)
        self.manager = self.mapper.get_manager(Group, ["ldap", "dn"])

    @staticmethod
    def name() -> str:
        return "groups"

    def get_objects(self, **kwargs) -> Generator:
        if not self._source.sync_groups:
            self._task.info("Group syncing is disabled for this Source")
            return iter(())
        return self.search_paginator(
            search_base=self.base_dn_groups,
            search_filter=self._source.group_object_filter,
            search_scope=SUBTREE,
            attributes=[
                ALL_ATTRIBUTES,
                ALL_OPERATIONAL_ATTRIBUTES,
                self._source.object_uniqueness_field,
            ],
            **kwargs,
        )

    def sync(self, page_data: list) -> int:
        """Iterate over all LDAP Groups and create authentik_core.Group instances"""
        if not self._source.sync_groups:
            self._task.info("Group syncing is disabled for this Source")
            return -1
        group_count = 0
        for group_data in page_data:
            if (attributes := self.get_attributes(group_data)) is None:
                continue
            group_dn = flatten(flatten(group_data.get("entryDN", group_data.get("dn"))))
            if not (uniq := self.get_identifier(attributes)):
                self._task.info(
                    f"Uniqueness field not found/not set in attributes: '{group_dn}'",
                    attributes=list(attributes.keys()),
                    dn=group_dn,
                )
                continue
            try:
                defaults = {
                    k: flatten(v)
                    for k, v in self.mapper.build_object_properties(
                        object_type=Group,
                        manager=self.manager,
                        user=None,
                        request=None,
                        dn=group_dn,
                        ldap=attributes,
                    ).items()
                }
                if "name" not in defaults:
                    raise IntegrityError("Name was not set by propertymappings")
                # Special check for `users` field, as this is an M2M relation, and cannot be sync'd
                if "users" in defaults:
                    del defaults["users"]
                parent = defaults.pop("parent", None)
                action, connection = self.matcher.get_group_action(uniq, defaults)

                created = False
                if action == Action.ENROLL:
                    # Legacy fallback, in case the group only has an `ldap_uniq` attribute set, but
                    # no source connection exists yet
                    legacy_group = Group.objects.filter(
                        **{
                            f"attributes__{LDAP_UNIQUENESS}": uniq,
                        }
                    ).first()
                    if legacy_group and LDAP_UNIQUENESS in legacy_group.attributes:
                        connection = GroupLDAPSourceConnection(
                            source=self._source,
                            group=legacy_group,
                            identifier=legacy_group.attributes.get(LDAP_UNIQUENESS),
                        )
                        group = legacy_group
                        # Switch the action to update the attributes
                        action = Action.AUTH
                    else:
                        group = Group.objects.create(**defaults)
                        created = True
                        connection.group = group
                    connection.save()

                if action in (Action.AUTH, Action.LINK):
                    group = connection.group
                    group.update_attributes(defaults)
                elif action == Action.DENY:
                    continue

                if parent:
                    group.parents.add(parent)
                self._logger.debug("Created group with attributes", **defaults)
            except SkipObjectException:
                continue
            except PropertyMappingExpressionException as exc:
                raise StopSync(exc, None, exc.mapping) from exc
            except (IntegrityError, FieldError, TypeError, AttributeError) as exc:
                self._logger.debug("failed to create group", exc=exc)
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=(
                        "Failed to create group; "
                        "To merge new group with existing group, connect it via the LDAP Source's "
                        "'Synced Groups' tab."
                    ),
                    exception=exception_to_dict(exc),
                    source=self._source,
                    dn=group_dn,
                ).save()
            else:
                self._logger.debug("Synced group", group=group.name, created=created)
                group_count += 1
        return group_count
