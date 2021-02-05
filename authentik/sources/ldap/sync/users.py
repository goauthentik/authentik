"""Sync LDAP Users into authentik"""
from typing import Any

import ldap3
import ldap3.core.exceptions
from django.db.utils import IntegrityError

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.core.models import User
from authentik.sources.ldap.auth import LDAP_DISTINGUISHED_NAME
from authentik.sources.ldap.models import LDAPPropertyMapping
from authentik.sources.ldap.sync.base import LDAP_UNIQUENESS, BaseLDAPSynchronizer


class UserLDAPSynchronizer(BaseLDAPSynchronizer):
    """Sync LDAP Users into authentik"""

    def sync(self) -> int:
        """Iterate over all LDAP Users and create authentik_core.User instances"""
        if not self._source.sync_users:
            self._logger.warning("User syncing is disabled for this Source")
            return -1
        users = self._source.connection.extend.standard.paged_search(
            search_base=self.base_dn_users,
            search_filter=self._source.user_object_filter,
            search_scope=ldap3.SUBTREE,
            attributes=[ldap3.ALL_ATTRIBUTES, ldap3.ALL_OPERATIONAL_ATTRIBUTES],
        )
        user_count = 0
        for user in users:
            self._logger.debug(user)
            attributes = user.get("attributes", {})
            user_dn = self._flatten(user.get("entryDN", ""))
            if self._source.object_uniqueness_field not in attributes:
                self._logger.warning(
                    "Cannot find uniqueness Field in attributes",
                    attributes=attributes.keys(),
                    dn=user_dn,
                )
                continue
            uniq = self._flatten(attributes[self._source.object_uniqueness_field])
            try:
                defaults = self._build_object_properties(user_dn, **attributes)
                self._logger.debug("Creating user with attributes", **defaults)
                if "username" not in defaults:
                    raise IntegrityError("Username was not set by propertymappings")
                user, created = User.objects.update_or_create(
                    **{
                        f"attributes__{LDAP_UNIQUENESS}": uniq,
                        "defaults": defaults,
                    }
                )
            except IntegrityError as exc:
                self._logger.warning("Failed to create user", exc=exc)
                self._logger.warning(
                    (
                        "To merge new User with existing user, set the User's "
                        f"Attribute '{LDAP_UNIQUENESS}' to '{uniq}'"
                    )
                )
            else:
                if created:
                    user.set_unusable_password()
                    user.save()
                self._logger.debug("Synced User", user=user.username, created=created)
                user_count += 1
        return user_count

    def _build_object_properties(
        self, user_dn: str, **kwargs
    ) -> dict[str, dict[Any, Any]]:
        properties = {"attributes": {}}
        for mapping in self._source.property_mappings.all().select_subclasses():
            if not isinstance(mapping, LDAPPropertyMapping):
                continue
            mapping: LDAPPropertyMapping
            try:
                value = mapping.evaluate(
                    user=None, request=None, ldap=kwargs, dn=user_dn
                )
                if value is None:
                    continue
                object_field = mapping.object_field
                if object_field.startswith("attributes."):
                    # Because returning a list might desired, we can't
                    # rely on self._flatten here. Instead, just save the result as-is
                    properties["attributes"][
                        object_field.replace("attributes.", "")
                    ] = value
                else:
                    properties[object_field] = self._flatten(value)
            except PropertyMappingExpressionException as exc:
                self._logger.warning(
                    "Mapping failed to evaluate", exc=exc, mapping=mapping
                )
                continue
        if self._source.object_uniqueness_field in kwargs:
            properties["attributes"][LDAP_UNIQUENESS] = self._flatten(
                kwargs.get(self._source.object_uniqueness_field)
            )
        properties["attributes"][LDAP_DISTINGUISHED_NAME] = user_dn
        return properties
