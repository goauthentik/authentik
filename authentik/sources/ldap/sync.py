"""Sync LDAP Users and groups into authentik"""
from typing import Any, Dict

import ldap3
import ldap3.core.exceptions
from django.db.utils import IntegrityError
from structlog.stdlib import get_logger

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.core.models import Group, User
from authentik.sources.ldap.models import LDAPPropertyMapping, LDAPSource

LOGGER = get_logger()


class LDAPSynchronizer:
    """Sync LDAP Users and groups into authentik"""

    _source: LDAPSource

    def __init__(self, source: LDAPSource):
        self._source = source

    @property
    def base_dn_users(self) -> str:
        """Shortcut to get full base_dn for user lookups"""
        if self._source.additional_user_dn:
            return f"{self._source.additional_user_dn},{self._source.base_dn}"
        return self._source.base_dn

    @property
    def base_dn_groups(self) -> str:
        """Shortcut to get full base_dn for group lookups"""
        if self._source.additional_group_dn:
            return f"{self._source.additional_group_dn},{self._source.base_dn}"
        return self._source.base_dn

    def sync_groups(self) -> int:
        """Iterate over all LDAP Groups and create authentik_core.Group instances"""
        if not self._source.sync_groups:
            LOGGER.warning("Group syncing is disabled for this Source")
            return -1
        groups = self._source.connection.extend.standard.paged_search(
            search_base=self.base_dn_groups,
            search_filter=self._source.group_object_filter,
            search_scope=ldap3.SUBTREE,
            attributes=ldap3.ALL_ATTRIBUTES,
        )
        group_count = 0
        for group in groups:
            attributes = group.get("attributes", {})
            if self._source.object_uniqueness_field not in attributes:
                LOGGER.warning(
                    "Cannot find uniqueness Field in attributes", user=attributes.keys()
                )
                continue
            uniq = attributes[self._source.object_uniqueness_field]
            _, created = Group.objects.update_or_create(
                attributes__ldap_uniq=uniq,
                parent=self._source.sync_parent_group,
                defaults={
                    "name": attributes.get("name", ""),
                    "attributes": {
                        "ldap_uniq": uniq,
                        "distinguishedName": attributes.get("distinguishedName"),
                    },
                },
            )
            LOGGER.debug(
                "Synced group", group=attributes.get("name", ""), created=created
            )
            group_count += 1
        return group_count

    def sync_users(self) -> int:
        """Iterate over all LDAP Users and create authentik_core.User instances"""
        if not self._source.sync_users:
            LOGGER.warning("User syncing is disabled for this Source")
            return -1
        users = self._source.connection.extend.standard.paged_search(
            search_base=self.base_dn_users,
            search_filter=self._source.user_object_filter,
            search_scope=ldap3.SUBTREE,
            attributes=ldap3.ALL_ATTRIBUTES,
        )
        user_count = 0
        for user in users:
            attributes = user.get("attributes", {})
            if self._source.object_uniqueness_field not in attributes:
                LOGGER.warning(
                    "Cannot find uniqueness Field in attributes", user=user.keys()
                )
                continue
            uniq = attributes[self._source.object_uniqueness_field]
            try:
                defaults = self._build_object_properties(attributes)
                user, created = User.objects.update_or_create(
                    attributes__ldap_uniq=uniq,
                    defaults=defaults,
                )
            except IntegrityError as exc:
                LOGGER.warning("Failed to create user", exc=exc)
                LOGGER.warning(
                    (
                        "To merge new User with existing user, set the User's "
                        f"Attribute 'ldap_uniq' to '{uniq}'"
                    )
                )
            else:
                if created:
                    user.set_unusable_password()
                    user.save()
                LOGGER.debug(
                    "Synced User", user=attributes.get("name", ""), created=created
                )
                user_count += 1
        return user_count

    def sync_membership(self):
        """Iterate over all Users and assign Groups using memberOf Field"""
        users = self._source.connection.extend.standard.paged_search(
            search_base=self.base_dn_users,
            search_filter=self._source.user_object_filter,
            search_scope=ldap3.SUBTREE,
            attributes=[
                self._source.user_group_membership_field,
                self._source.object_uniqueness_field,
            ],
        )
        group_cache: Dict[str, Group] = {}
        for user in users:
            member_of = user.get("attributes", {}).get(
                self._source.user_group_membership_field, []
            )
            uniq = user.get("attributes", {}).get(
                self._source.object_uniqueness_field, []
            )
            for group_dn in member_of:
                # Check if group_dn is within our base_dn_groups, and skip if not
                if not group_dn.endswith(self.base_dn_groups):
                    continue
                # Check if we fetched the group already, and if not cache it for later
                if group_dn not in group_cache:
                    groups = Group.objects.filter(
                        attributes__distinguishedName=group_dn
                    )
                    if not groups.exists():
                        LOGGER.warning(
                            "Group does not exist in our DB yet, run sync_groups first.",
                            group=group_dn,
                        )
                        return
                    group_cache[group_dn] = groups.first()
                group = group_cache[group_dn]
                users = User.objects.filter(attributes__ldap_uniq=uniq)
                group.users.add(*list(users))
        # Now that all users are added, lets write everything
        for _, group in group_cache.items():
            group.save()
        LOGGER.debug("Successfully updated group membership")

    def _build_object_properties(
        self, attributes: Dict[str, Any]
    ) -> Dict[str, Dict[Any, Any]]:
        properties = {"attributes": {}}
        for mapping in self._source.property_mappings.all().select_subclasses():
            if not isinstance(mapping, LDAPPropertyMapping):
                continue
            mapping: LDAPPropertyMapping
            try:
                value = mapping.evaluate(user=None, request=None, ldap=attributes)
                if value is None:
                    continue
                object_field = mapping.object_field
                if object_field.startswith("attributes."):
                    properties["attributes"][
                        object_field.replace("attributes.", "")
                    ] = value
                else:
                    properties[object_field] = value
            except PropertyMappingExpressionException as exc:
                LOGGER.warning("Mapping failed to evaluate", exc=exc, mapping=mapping)
                continue
        if self._source.object_uniqueness_field in attributes:
            properties["attributes"]["ldap_uniq"] = attributes.get(
                self._source.object_uniqueness_field
            )
        properties["attributes"]["distinguishedName"] = attributes.get(
            "distinguishedName"
        )
        return properties
