"""Sync LDAP Users and groups into authentik"""
import ldap3
import ldap3.core.exceptions
from django.db.utils import IntegrityError

from authentik.core.models import Group
from authentik.sources.ldap.sync.base import LDAP_UNIQUENESS, BaseLDAPSynchronizer


class GroupLDAPSynchronizer(BaseLDAPSynchronizer):
    """Sync LDAP Users and groups into authentik"""

    def sync(self) -> int:
        """Iterate over all LDAP Groups and create authentik_core.Group instances"""
        if not self._source.sync_groups:
            self._logger.warning("Group syncing is disabled for this Source")
            return -1
        groups = self._source.connection.extend.standard.paged_search(
            search_base=self.base_dn_groups,
            search_filter=self._source.group_object_filter,
            search_scope=ldap3.SUBTREE,
            attributes=[ldap3.ALL_ATTRIBUTES, ldap3.ALL_OPERATIONAL_ATTRIBUTES],
        )
        group_count = 0
        for group in groups:
            attributes = group.get("attributes", {})
            group_dn = self._flatten(
                self._flatten(group.get("entryDN", group.get("dn")))
            )
            if self._source.object_uniqueness_field not in attributes:
                self._logger.warning(
                    "Cannot find uniqueness Field in attributes",
                    attributes=attributes.keys(),
                    dn=group_dn,
                )
                continue
            uniq = self._flatten(attributes[self._source.object_uniqueness_field])
            try:
                defaults = self.build_group_properties(group_dn, **attributes)
                self._logger.debug("Creating group with attributes", **defaults)
                if "name" not in defaults:
                    raise IntegrityError("Name was not set by propertymappings")
                ak_group, created = Group.objects.update_or_create(
                    **{
                        f"attributes__{LDAP_UNIQUENESS}": uniq,
                        "parent": self._source.sync_parent_group,
                        "defaults": defaults,
                    }
                )
            except IntegrityError as exc:
                self._logger.warning("Failed to create group", exc=exc)
                self._logger.warning(
                    (
                        "To merge new group with existing group, set the group's "
                        f"Attribute '{LDAP_UNIQUENESS}' to '{uniq}'"
                    )
                )
            else:
                self._logger.debug("Synced group", group=ak_group.name, created=created)
                group_count += 1
        return group_count
