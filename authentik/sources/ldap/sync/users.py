"""Sync LDAP Users into authentik"""
from typing import Generator

from django.core.exceptions import FieldError
from django.db.utils import IntegrityError
from ldap3 import ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, SUBTREE

from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.sources.ldap.sync.base import LDAP_UNIQUENESS, BaseLDAPSynchronizer
from authentik.sources.ldap.sync.vendor.freeipa import FreeIPA
from authentik.sources.ldap.sync.vendor.ms_ad import MicrosoftActiveDirectory


class UserLDAPSynchronizer(BaseLDAPSynchronizer):
    """Sync LDAP Users into authentik"""

    @staticmethod
    def name() -> str:
        return "users"

    def get_objects(self, **kwargs) -> Generator:
        if not self._source.sync_users:
            self.message("User syncing is disabled for this Source")
            return iter(())
        return self.search_paginator(
            search_base=self.base_dn_users,
            search_filter=self._source.user_object_filter,
            search_scope=SUBTREE,
            attributes=[ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES],
            **kwargs,
        )

    def sync(self, page_data: list) -> int:
        """Iterate over all LDAP Users and create authentik_core.User instances"""
        if not self._source.sync_users:
            self.message("User syncing is disabled for this Source")
            return -1
        user_count = 0
        for user in page_data:
            if "attributes" not in user:
                continue
            attributes = user.get("attributes", {})
            user_dn = self._flatten(user.get("entryDN", user.get("dn")))
            if self._source.object_uniqueness_field not in attributes:
                self.message(
                    f"Cannot find uniqueness field in attributes: '{user_dn}'",
                    attributes=attributes.keys(),
                    dn=user_dn,
                )
                continue
            uniq = self._flatten(attributes[self._source.object_uniqueness_field])
            try:
                defaults = self.build_user_properties(user_dn, **attributes)
                self._logger.debug("Writing user with attributes", **defaults)
                if "username" not in defaults:
                    raise IntegrityError("Username was not set by propertymappings")
                ak_user, created = self.update_or_create_attributes(
                    User, {f"attributes__{LDAP_UNIQUENESS}": uniq}, defaults
                )
            except (IntegrityError, FieldError, TypeError, AttributeError) as exc:
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=(
                        f"Failed to create user: {str(exc)} "
                        "To merge new user with existing user, set the user's "
                        f"Attribute '{LDAP_UNIQUENESS}' to '{uniq}'"
                    ),
                    source=self._source,
                    dn=user_dn,
                ).save()
            else:
                self._logger.debug("Synced User", user=ak_user.username, created=created)
                user_count += 1
                MicrosoftActiveDirectory(self._source).sync(attributes, ak_user, created)
                FreeIPA(self._source).sync(attributes, ak_user, created)
        return user_count
