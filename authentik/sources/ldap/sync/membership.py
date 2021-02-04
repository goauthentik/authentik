"""Sync LDAP Users and groups into authentik"""
from typing import Any, Optional

import ldap3
import ldap3.core.exceptions

from authentik.core.models import Group, User
from authentik.sources.ldap.auth import LDAP_DISTINGUISHED_NAME
from authentik.sources.ldap.models import LDAPSource
from authentik.sources.ldap.sync.base import LDAP_UNIQUENESS, BaseLDAPSynchronizer


class MembershipLDAPSynchronizer(BaseLDAPSynchronizer):
    """Sync LDAP Users and groups into authentik"""

    group_cache: dict[str, Group]

    def __init__(self, source: LDAPSource):
        super().__init__(source)
        self.group_cache: dict[str, Group] = {}

    def sync(self):
        """Iterate over all Users and assign Groups using memberOf Field"""
        groups = self._source.connection.extend.standard.paged_search(
            search_base=self.base_dn_groups,
            search_filter=self._source.group_object_filter,
            search_scope=ldap3.SUBTREE,
            attributes=[
                self._source.group_membership_field,
                self._source.object_uniqueness_field,
            ],
        )
        for group in groups:
            members = group.get("attributes", {}).get(
                self._source.group_membership_field, []
            )
            users = User.objects.filter(
                **{f"attributes__{LDAP_DISTINGUISHED_NAME}__in": members}
            )

            ak_group = self.get_group(group)
            if not ak_group:
                continue
            ak_group.users.set(users)
            ak_group.save()
        self._logger.debug("Successfully updated group membership")

    def get_group(self, group_dict: dict[str, Any]) -> Optional[Group]:
        """Check if we fetched the group already, and if not cache it for later"""
        group_uniq = group_dict.get("attributes", {}).get(LDAP_UNIQUENESS, "")
        group_dn = group_dict.get("attributes", {}).get(LDAP_DISTINGUISHED_NAME, "")
        if group_uniq not in self.group_cache:
            groups = Group.objects.filter(
                **{f"attributes__{LDAP_UNIQUENESS}": group_uniq}
            )
            if not groups.exists():
                self._logger.warning(
                    "Group does not exist in our DB yet, run sync_groups first.",
                    group=group_dn,
                )
                return None
            self.group_cache[group_uniq] = groups.first()
        return self.group_cache[group_uniq]
