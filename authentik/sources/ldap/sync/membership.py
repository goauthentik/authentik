"""Sync LDAP Users and groups into authentik"""

from collections.abc import Generator
from typing import Any

from django.db.models import Q
from ldap3 import SUBTREE
from ldap3.utils.conv import escape_filter_chars

from authentik.core.models import Group, User
from authentik.sources.ldap.models import (
    LDAP_DISTINGUISHED_NAME,
    GroupLDAPSourceConnection,
    LDAPSource,
    UserLDAPSourceConnection,
)
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer
from authentik.tasks.models import Task


class BaseMembershipLDAPSynchronizer(BaseLDAPSynchronizer):
    """Sync membership of LDAP Users and Groups into authentik"""

    user_cache: dict[str, User]
    group_cache: dict[str, Group]

    def __init__(self, source: LDAPSource, task: Task):
        super().__init__(source, task)
        self.user_cache: dict[str, User] = {}
        self.group_cache: dict[str, Group] = {}

    @staticmethod
    def name() -> str:
        raise NotImplementedError

    def get_objects(self, **kwargs) -> Generator:
        raise NotImplementedError

    def sync(self, page_data: list) -> int:
        raise NotImplementedError

    def get_user(self, user_dict: dict[str, Any]) -> User | None:
        """Check if we fetched the user already, and if not cache it for later"""
        user_dn = user_dict.get("dn", {})
        user_uniq = user_dict.get("attributes", {}).get(self._source.object_uniqueness_field, [])
        # user_uniq might be a single string or an array with (hopefully) a single string
        if isinstance(user_uniq, list):
            if len(user_uniq) < 1:
                self._task.info(
                    f"User does not have a uniqueness attribute: '{user_dn}'",
                    user=user_dn,
                )
                return None
            user_uniq = user_uniq[0]
        if user_uniq not in self.user_cache:
            users = UserLDAPSourceConnection.objects.filter(identifier=user_uniq).select_related(
                "user"
            )
            if not users.exists():
                self._task.info(
                    f"User does not exist in our DB yet, run sync_users first: '{user_dn}'",
                    user=user_dn,
                )
                return None
            self.user_cache[user_uniq] = users.first()
        return self.user_cache[user_uniq]

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
            groups = GroupLDAPSourceConnection.objects.filter(identifier=group_uniq).select_related(
                "group"
            )
            if not groups.exists():
                if self._source.sync_groups:
                    self._task.info(
                        f"Group does not exist in our DB yet, run sync_groups first: '{group_dn}'",
                        group=group_dn,
                    )
                return None
            self.group_cache[group_uniq] = groups.first().group
        return self.group_cache[group_uniq]


class MembershipLDAPSynchronizer(BaseMembershipLDAPSynchronizer):
    """Sync membership of LDAP Users into authentik"""

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
        for group_data in page_data:
            if self._source.lookup_groups_from_user:
                group_dn = group_data.get("dn", {})
                escaped_dn = escape_filter_chars(group_dn)
                group_filter = f"({self._source.group_membership_field}={escaped_dn})"
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
                if (attributes := self.get_attributes(group_data)) is None:
                    continue
                members = attributes.get(self._source.group_membership_field, [])

            group = self.get_group(group_data)
            if not group:
                continue

            users = User.objects.filter(
                Q(**{f"attributes__{self._source.user_membership_attribute}__in": members})
                | Q(
                    **{
                        f"attributes__{self._source.user_membership_attribute}__isnull": True,
                        "groups__in": [group],
                    }
                )
            ).distinct()
            membership_count += 1
            membership_count += users.count()
            group.users.set(users)
            group.save()
        self._logger.debug("Successfully updated group membership")
        return membership_count


class ParentshipLDAPSynchronizer(BaseMembershipLDAPSynchronizer):
    """Sync parentship of LDAP Groups into authentik"""

    @staticmethod
    def name() -> str:
        return "parentship"

    def get_objects(self, **kwargs) -> Generator:
        if not self._source.sync_groups:
            self._task.info("Group syncing is disabled for this Source")
            return iter(())
        if not self._source.sync_group_hierarchy:
            self._task.info("Group hierarchy syncing is disabled for this Source")
            return iter(())

        attributes = [
            self._source.group_membership_field,
            self._source.user_membership_attribute,
            self._source.object_uniqueness_field,
            LDAP_DISTINGUISHED_NAME,
        ]

        return self.search_paginator(
            search_base=self.base_dn_groups,
            search_filter=self._source.group_object_filter,
            search_scope=SUBTREE,
            attributes=attributes,
            **kwargs,
        )

    def sync(self, page_data: list) -> int:
        """Iterate over all Groups and assign their parents"""
        if not self._source.sync_groups:
            self._task.info("Group syncing is disabled for this Source")
            return -1
        if not self._source.sync_group_hierarchy:
            self._task.info("Group hierarchy syncing is disabled for this Source")
            return -1
        count = 0
        for group_data in page_data:
            if (attributes := self.get_attributes(group_data)) is None:
                continue
            group = self.get_group(group_data)
            if not group:
                continue

            # Deliberately WET
            if self._source.lookup_groups_from_user:
                parents_from_source_raw = attributes.get(self._source.group_membership_field, [])
                parents_from_source = Group.objects.filter(
                    **{
                        (
                            "attributes__" f"{self._source.user_membership_attribute}__in"
                        ): parents_from_source_raw
                    }
                )
                parents_not_from_source = group.parents.exclude(
                    groupsourceconnection__source=self._source
                )

                count = len(parents_from_source)
                group.parents.set(parents_from_source.union(parents_not_from_source))
            else:
                children_from_source_raw = attributes.get(self._source.group_membership_field, [])
                children_from_source = Group.objects.filter(
                    **{
                        (
                            "attributes__" f"{self._source.user_membership_attribute}__in"
                        ): children_from_source_raw
                    }
                )
                children_not_from_source = group.children.exclude(
                    groupsourceconnection__source=self._source
                )

                count = len(children_from_source)
                group.children.set(children_from_source.union(children_not_from_source))

        self._logger.debug("Successfully updated group parentship")
        return count
