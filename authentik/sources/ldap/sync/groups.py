"""Sync LDAP Users and groups into authentik"""
import ldap3
import ldap3.core.exceptions

from authentik.core.models import Group
from authentik.sources.ldap.auth import LDAP_DISTINGUISHED_NAME
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
            group_dn = self._flatten(group.get("entryDN", ""))
            if self._source.object_uniqueness_field not in attributes:
                self._logger.warning(
                    "Cannot find uniqueness Field in attributes",
                    attributes=attributes.keys(),
                    dn=group_dn,
                )
                continue
            uniq = attributes[self._source.object_uniqueness_field]
            # TODO: Use Property Mappings
            name = self._flatten(attributes.get("name", ""))
            _, created = Group.objects.update_or_create(
                **{
                    f"attributes__{LDAP_UNIQUENESS}": uniq,
                    "parent": self._source.sync_parent_group,
                    "defaults": {
                        "name": name,
                        "attributes": {
                            LDAP_UNIQUENESS: uniq,
                            LDAP_DISTINGUISHED_NAME: group_dn,
                        },
                    },
                }
            )
            self._logger.debug(
                "Synced group", group=name, created=created
            )
            group_count += 1
        return group_count
