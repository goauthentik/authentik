"""Sync LDAP Users into authentik"""
from datetime import datetime

import ldap3
import ldap3.core.exceptions
from django.db.utils import IntegrityError
from pytz import UTC

from authentik.core.models import User
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
            attributes = user.get("attributes", {})
            user_dn = self._flatten(user.get("entryDN", user.get("dn")))
            if self._source.object_uniqueness_field not in attributes:
                self._logger.warning(
                    "Cannot find uniqueness Field in attributes",
                    attributes=attributes.keys(),
                    dn=user_dn,
                )
                continue
            uniq = self._flatten(attributes[self._source.object_uniqueness_field])
            try:
                defaults = self.build_user_properties(user_dn, **attributes)
                self._logger.debug("Creating user with attributes", **defaults)
                if "username" not in defaults:
                    raise IntegrityError("Username was not set by propertymappings")
                ak_user, created = User.objects.update_or_create(
                    **{
                        f"attributes__{LDAP_UNIQUENESS}": uniq,
                        "defaults": defaults,
                    }
                )
            except IntegrityError as exc:
                self._logger.warning("Failed to create user", exc=exc)
                self._logger.warning(
                    (
                        "To merge new user with existing user, set the user's "
                        f"Attribute '{LDAP_UNIQUENESS}' to '{uniq}'"
                    )
                )
            else:
                self._logger.debug(
                    "Synced User", user=ak_user.username, created=created
                )
                user_count += 1
                # pylint: disable=no-value-for-parameter
                pwd_last_set = UTC.localize(
                    attributes.get("pwdLastSet", datetime.now())
                )
                if created or pwd_last_set >= ak_user.password_change_date:
                    self._logger.debug(
                        "Reset user's password",
                        user=ak_user.username,
                        created=created,
                        pwd_last_set=pwd_last_set,
                    )
                    ak_user.set_unusable_password()
                    ak_user.save()
        return user_count
