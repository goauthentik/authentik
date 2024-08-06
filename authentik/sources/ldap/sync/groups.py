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
from authentik.events.models import Event, EventAction
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.sources.ldap.models import LDAP_UNIQUENESS, LDAPSource, flatten
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer


class GroupLDAPSynchronizer(BaseLDAPSynchronizer):
    """Sync LDAP Users and groups into authentik"""

    def __init__(self, source: LDAPSource):
        super().__init__(source)
        self.mapper = SourceMapper(source)
        self.manager = self.mapper.get_manager(Group, ["ldap", "dn"])

    @staticmethod
    def name() -> str:
        return "groups"

    def get_objects(self, **kwargs) -> Generator:
        if not self._source.sync_groups:
            self.message("Group syncing is disabled for this Source")
            return iter(())
        return self.search_paginator(
            search_base=self.base_dn_groups,
            search_filter=self._source.group_object_filter,
            search_scope=SUBTREE,
            attributes=[ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES],
            **kwargs,
        )

    def sync(self, page_data: list) -> int:
        """Iterate over all LDAP Groups and create authentik_core.Group instances"""
        if not self._source.sync_groups:
            self.message("Group syncing is disabled for this Source")
            return -1
        group_count = 0
        for group in page_data:
            if "attributes" not in group:
                continue
            attributes = group.get("attributes", {})
            group_dn = flatten(flatten(group.get("entryDN", group.get("dn"))))
            if self._source.object_uniqueness_field not in attributes:
                self.message(
                    f"Cannot find uniqueness field in attributes: '{group_dn}'",
                    attributes=attributes.keys(),
                    dn=group_dn,
                )
                continue
            uniq = flatten(attributes[self._source.object_uniqueness_field])
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
                ak_group, created = Group.update_or_create_attributes(
                    {
                        f"attributes__{LDAP_UNIQUENESS}": uniq,
                    },
                    defaults,
                )
                self._logger.debug("Created group with attributes", **defaults)
            except SkipObjectException:
                continue
            except PropertyMappingExpressionException as exc:
                raise StopSync(exc, None, exc.mapping) from exc
            except (IntegrityError, FieldError, TypeError, AttributeError) as exc:
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=(
                        f"Failed to create group: {str(exc)} "
                        "To merge new group with existing group, set the groups's "
                        f"Attribute '{LDAP_UNIQUENESS}' to '{uniq}'"
                    ),
                    source=self._source,
                    dn=group_dn,
                ).save()
            else:
                self._logger.debug("Synced group", group=ak_group.name, created=created)
                group_count += 1
        return group_count
