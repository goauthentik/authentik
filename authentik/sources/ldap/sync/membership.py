"""Sync LDAP Users and groups into authentik"""

from collections.abc import Generator
from typing import Any

from django.db.models import Q
from ldap3 import SUBTREE

from authentik.core.models import Group, User
from authentik.sources.ldap.models import LDAP_DISTINGUISHED_NAME, LDAP_UNIQUENESS, LDAPSource
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer
from authentik.tasks.models import Task


class MembershipLDAPSynchronizer(BaseLDAPSynchronizer):
    """Sync LDAP Users and groups into authentik"""

    group_cache: dict[str, Group]

    def __init__(self, source: LDAPSource, task: Task):
        super().__init__(source, task)
        self.group_cache: dict[str, Group] = {}

    @staticmethod
    def name() -> str:
        return "membership"

    def get_objects(self, **kwargs) -> Generator:
        if not self._source.sync_groups:
            self._task.info("Group syncing is disabled for this Source")
            return iter(())

        # If we are looking up groups from users, we don't need to fetch the group membership field
        attributes = [self._source.object_uniqueness_field, LDAP_DISTINGUISHED_NAME]
        if not self._source.lookup_groups_from_user:
            attributes.append(self._source.group_membership_field)

        return self.search_paginator(
            search_base=self.base_dn_groups,
            search_filter=self._source.group_object_filter,
            search_scope=SUBTREE,
            attributes=attributes,
            **kwargs,
        )

    def sync(self, page_data: list) -> int:
        """Iterate over all Users and assign Groups using memberOf Field"""
        if not self._source.sync_groups:
            self._task.info("Group syncing is disabled for this Source")
            return -1
        membership_count = 0
        for group in page_data:
            if self._source.lookup_groups_from_user:
                group_dn = group.get("dn", {})
                group_filter = f"({self._source.group_membership_field}={group_dn})"
                group_members = self._source.connection().extend.standard.paged_search(
                    search_base=self.base_dn_users,
                    search_filter=group_filter,
                    search_scope=SUBTREE,
                    attributes=[self._source.object_uniqueness_field],
                )
                members = []
                for group_member in group_members:
                    group_member_dn = group_member.get("dn", {})
                    members.append(group_member_dn)
            else:
                if (attributes := self.get_attributes(group)) is None:
                    continue
                members = attributes.get(self._source.group_membership_field, [])

            ak_group = self.get_group(group)
            if not ak_group:
                continue

            users = User.objects.filter(
                Q(**{f"attributes__{self._source.user_membership_attribute}__in": members})
                | Q(
                    **{
                        f"attributes__{self._source.user_membership_attribute}__isnull": True,
                        "ak_groups__in": [ak_group],
                    }
                )
            ).distinct()
            membership_count += 1
            membership_count += users.count()
            ak_group.users.set(users)
            ak_group.save()
        self._logger.debug("Successfully updated group membership")
        return membership_count

    def get_group(self, group_dict: dict[str, Any]) -> Group | None:
        """Check if we fetched the group already, and if not cache it for later"""
        group_dn = group_dict.get("attributes", {}).get(LDAP_DISTINGUISHED_NAME, [])
        group_uniq = group_dict.get("attributes", {}).get(self._source.object_uniqueness_field, [])
        # group_uniq might be a single string or an array with (hopefully) a single string
        if isinstance(group_uniq, list):
            if len(group_uniq) < 1:
                self._task.info(
                    f"Group does not have a uniqueness attribute: '{group_dn}'",
                    group=group_dn,
                )
                return None
            group_uniq = group_uniq[0]
        if group_uniq not in self.group_cache:
            groups = Group.objects.filter(**{f"attributes__{LDAP_UNIQUENESS}": group_uniq})
            if not groups.exists():
                if self._source.sync_groups:
                    self._task.info(
                        f"Group does not exist in our DB yet, run sync_groups first: '{group_dn}'",
                        group=group_dn,
                    )
                return None
            self.group_cache[group_uniq] = groups.first()
        return self.group_cache[group_uniq]
