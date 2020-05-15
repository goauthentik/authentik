"""Wrapper for ldap3 to easily manage user"""
from typing import Any, Dict, Optional

import ldap3
import ldap3.core.exceptions
from django.db.utils import IntegrityError
from structlog import get_logger

from passbook.channels.in_ldap.models import LDAPInlet, LDAPPropertyMapping
from passbook.core.exceptions import PropertyMappingExpressionException
from passbook.core.models import Group, User

LOGGER = get_logger()


class Connector:
    """Wrapper for ldap3 to easily manage user authentication and creation"""

    _server: ldap3.Server
    _connection = ldap3.Connection
    _inlet: LDAPInlet

    def __init__(self, source: LDAPInlet):
        self._inlet = source
        self._server = ldap3.Server(source.server_uri)  # Implement URI parsing

    def bind(self):
        """Bind using Inlet's Credentials"""
        self._connection = ldap3.Connection(
            self._server,
            raise_exceptions=True,
            user=self._inlet.bind_cn,
            password=self._inlet.bind_password,
        )

        self._connection.bind()
        if self._inlet.start_tls:
            self._connection.start_tls()

    @staticmethod
    def encode_pass(password: str) -> bytes:
        """Encodes a plain-text password so it can be used by AD"""
        return '"{}"'.format(password).encode("utf-16-le")

    @property
    def base_dn_users(self) -> str:
        """Shortcut to get full base_dn for user lookups"""
        return ",".join([self._inlet.additional_user_dn, self._inlet.base_dn])

    @property
    def base_dn_groups(self) -> str:
        """Shortcut to get full base_dn for group lookups"""
        return ",".join([self._inlet.additional_group_dn, self._inlet.base_dn])

    def sync_groups(self):
        """Iterate over all LDAP Groups and create passbook_core.Group instances"""
        if not self._inlet.sync_groups:
            LOGGER.debug("Group syncing is disabled for this Inlet")
            return
        groups = self._connection.extend.standard.paged_search(
            search_base=self.base_dn_groups,
            search_filter=self._inlet.group_object_filter,
            search_scope=ldap3.SUBTREE,
            attributes=ldap3.ALL_ATTRIBUTES,
        )
        for group in groups:
            attributes = group.get("attributes", {})
            _, created = Group.objects.update_or_create(
                attributes__ldap_uniq=attributes.get(
                    self._inlet.object_uniqueness_field, ""
                ),
                parent=self._inlet.sync_parent_group,
                # defaults=self._build_object_properties(attributes),
                defaults={
                    "name": attributes.get("name", ""),
                    "attributes": {
                        "ldap_uniq": attributes.get(
                            self._inlet.object_uniqueness_field, ""
                        ),
                        "distinguishedName": attributes.get("distinguishedName"),
                    },
                },
            )
            LOGGER.debug(
                "Synced group", group=attributes.get("name", ""), created=created
            )

    def sync_users(self):
        """Iterate over all LDAP Users and create passbook_core.User instances"""
        users = self._connection.extend.standard.paged_search(
            search_base=self.base_dn_users,
            search_filter=self._inlet.user_object_filter,
            search_scope=ldap3.SUBTREE,
            attributes=ldap3.ALL_ATTRIBUTES,
        )
        for user in users:
            attributes = user.get("attributes", {})
            try:
                uniq = attributes[self._inlet.object_uniqueness_field]
            except KeyError:
                LOGGER.warning("Cannot find uniqueness Field in attributes")
                continue
            try:
                user, created = User.objects.update_or_create(
                    attributes__ldap_uniq=uniq,
                    defaults=self._build_object_properties(attributes),
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

    def sync_membership(self):
        """Iterate over all Users and assign Groups using memberOf Field"""
        users = self._connection.extend.standard.paged_search(
            search_base=self.base_dn_users,
            search_filter=self._inlet.user_object_filter,
            search_scope=ldap3.SUBTREE,
            attributes=[
                self._inlet.user_group_membership_field,
                self._inlet.object_uniqueness_field,
            ],
        )
        group_cache: Dict[str, Group] = {}
        for user in users:
            member_of = user.get("attributes", {}).get(
                self._inlet.user_group_membership_field, []
            )
            uniq = user.get("attributes", {}).get(
                self._inlet.object_uniqueness_field, []
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
                group.user_set.add(*list(users))
        # Now that all users are added, lets write everything
        for _, group in group_cache.items():
            group.save()
        LOGGER.debug("Successfully updated group membership")

    def _build_object_properties(
        self, attributes: Dict[str, Any]
    ) -> Dict[str, Dict[Any, Any]]:
        properties = {"attributes": {}}
        for mapping in self._inlet.property_mappings.all().select_subclasses():
            if not isinstance(mapping, LDAPPropertyMapping):
                continue
            mapping: LDAPPropertyMapping
            try:
                properties[mapping.object_field] = mapping.evaluate(
                    user=None, request=None, ldap=attributes
                )
            except PropertyMappingExpressionException as exc:
                LOGGER.warning("Mapping failed to evaluate", exc=exc, mapping=mapping)
                continue
        if self._inlet.object_uniqueness_field in attributes:
            properties["attributes"]["ldap_uniq"] = attributes.get(
                self._inlet.object_uniqueness_field
            )
        properties["attributes"]["distinguishedName"] = attributes.get(
            "distinguishedName"
        )
        return properties

    def auth_user(self, password: str, **filters: Dict[str, str]) -> Optional[User]:
        """Try to bind as either user_dn or mail with password.
        Returns True on success, otherwise False"""
        users = User.objects.filter(**filters)
        if not users.exists():
            return None
        user: User = users.first()
        if "distinguishedName" not in user.attributes:
            LOGGER.debug(
                "User doesn't have DN set, assuming not LDAP imported.", user=user
            )
            return None
        # Either has unusable password,
        # or has a password, but couldn't be authenticated by ModelBackend.
        # This means we check with a bind to see if the LDAP password has changed
        if self.auth_user_by_bind(user, password):
            # Password given successfully binds to LDAP, so we save it in our Database
            LOGGER.debug("Updating user's password in DB", user=user)
            user.set_password(password)
            user.save()
            return user
        # Password doesn't match
        LOGGER.debug("Failed to bind, password invalid")
        return None

    def auth_user_by_bind(self, user: User, password: str) -> Optional[User]:
        """Attempt authentication by binding to the LDAP server as `user`. This
        method should be avoided as its slow to do the bind."""
        # Try to bind as new user
        LOGGER.debug("Attempting Binding as user", user=user)
        try:
            temp_connection = ldap3.Connection(
                self._server,
                user=user.attributes.get("distinguishedName"),
                password=password,
                raise_exceptions=True,
            )
            temp_connection.bind()
            return user
        except ldap3.core.exceptions.LDAPInvalidCredentialsResult as exception:
            LOGGER.debug("LDAPInvalidCredentialsResult", user=user, error=exception)
        except ldap3.core.exceptions.LDAPException as exception:
            LOGGER.warning(exception)
        return None
