"""Sync LDAP Users and groups into authentik"""
from typing import Any, Optional

import ldap3
import ldap3.core.exceptions
from django.db.models import Q

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

    def sync(self) -> int:
        """Iterate over all Users and assign Groups using memberOf Field"""
        if not self._source.sync_groups:
            self.message("Group syncing is disabled for this Source")
            return -1
        groups = self._source.connection.extend.standard.paged_search(
            search_base=self.base_dn_groups,
            search_filter=self._source.group_object_filter,
            search_scope=ldap3.SUBTREE,
            attributes=[
                self._source.group_membership_field,
                self._source.object_uniqueness_field,
                LDAP_DISTINGUISHED_NAME,
            ],
        )
        membership_count = 0
        for group in groups:
            members = group.get("attributes", {}).get(self._source.group_membership_field, [])
            ak_group = self.get_group(group)
            if not ak_group:
                continue

            membership_mapping_attribute = LDAP_DISTINGUISHED_NAME
            if self._source.group_membership_field == "memberUid":
                # If memberships are based on the posixGroup's 'memberUid'
                # attribute we use the RDN instead of the FDN to lookup members.
                membership_mapping_attribute = LDAP_UNIQUENESS

            users = User.objects.filter(
                Q(**{f"attributes__{membership_mapping_attribute}__in": members})
                | Q(
                    **{
                        f"attributes__{membership_mapping_attribute}__isnull": True,
                        "ak_groups__in": [ak_group],
                    }
                )
            )
            membership_count += 1
            membership_count += users.count()
            ak_group.users.set(users)
            ak_group.save()
        self._logger.debug("Successfully updated group membership")
        return membership_count

    def get_group(self, group_dict: dict[str, Any]) -> Optional[Group]:
        """Check if we fetched the group already, and if not cache it for later"""
        group_dn = group_dict.get("attributes", {}).get(LDAP_DISTINGUISHED_NAME, [])
        group_uniq = group_dict.get("attributes", {}).get(self._source.object_uniqueness_field, [])
        # group_uniq might be a single string or an array with (hopefully) a single string
        if isinstance(group_uniq, list):
            if len(group_uniq) < 1:
                self.message(
                    f"Group does not have a uniqueness attribute: '{group_dn}'",
                    group=group_dn,
                )
                return None
            group_uniq = group_uniq[0]
        if group_uniq not in self.group_cache:
            groups = Group.objects.filter(**{f"attributes__{LDAP_UNIQUENESS}": group_uniq})
            if not groups.exists():
                if self._source.sync_groups:
                    self.message(
                        f"Group does not exist in our DB yet, run sync_groups first: '{group_dn}'",
                        group=group_dn,
                    )
                return None
            self.group_cache[group_uniq] = groups.first()
        return self.group_cache[group_uniq]
