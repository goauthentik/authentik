"""Wrapper for ldap3 to easily manage user"""
from typing import Any, Dict, Optional

import ldap3
import ldap3.core.exceptions
from structlog import get_logger

from passbook.core.models import Group, User
from passbook.sources.ldap.models import LDAPSource

LOGGER = get_logger()


class Connector:
    """Wrapper for ldap3 to easily manage user authentication and creation"""

    _server: ldap3.Server
    _connection = ldap3.Connection
    _source: LDAPSource

    def __init__(self, source: LDAPSource):
        self._source = source
        self._server = ldap3.Server(source.server_uri) # Implement URI parsing

    def bind(self):
        """Bind using Source's Credentials"""
        self._connection = ldap3.Connection(self._server, raise_exceptions=True,
                                            user=self._source.bind_cn,
                                            password=self._source.bind_password)

        self._connection.bind()
        if self._source.start_tls:
            self._connection.start_tls()

    @staticmethod
    def encode_pass(password: str) -> bytes:
        """Encodes a plain-text password so it can be used by AD"""
        return '"{}"'.format(password).encode('utf-16-le')

    @property
    def base_dn_users(self) -> str:
        """Shortcut to get full base_dn for user lookups"""
        return ','.join([self._source.additional_user_dn, self._source.base_dn])

    @property
    def base_dn_groups(self) -> str:
        """Shortcut to get full base_dn for group lookups"""
        return ','.join([self._source.additional_group_dn, self._source.base_dn])

    def sync_groups(self):
        """Iterate over all LDAP Groups and create passbook_core.Group instances"""
        attributes = [
            'objectSid', # Used as unique Identifier
            'name',
            'dn',
        ]
        groups = self._connection.extend.standard.paged_search(
            search_base=self.base_dn_groups,
            search_filter=self._source.group_object_filter,
            search_scope=ldap3.SUBTREE,
            attributes=ldap3.ALL_ATTRIBUTES)
        for group in groups:
            attributes = group.get('attributes', {})
            _, created = Group.objects.update_or_create(
                attributes__objectSid=attributes.get('objectSid', ''),
                defaults=self._build_object_properties(attributes),
            )
            LOGGER.debug("Synced group", group=attributes.get('name', ''), created=created)

    def sync_users(self):
        """Iterate over all LDAP Users and create passbook_core.User instances"""
        users = self._connection.extend.standard.paged_search(
            search_base=self.base_dn_users,
            search_filter=self._source.user_object_filter,
            search_scope=ldap3.SUBTREE,
            attributes=ldap3.ALL_ATTRIBUTES)
        for user in users:
            attributes = user.get('attributes', {})
            _, created = User.objects.update_or_create(
                attributes__objectSid=attributes.get('objectSid', ''),
                defaults=self._build_object_properties(attributes),
            )
            LOGGER.debug("Synced User", user=attributes.get('name', ''), created=created)

    def sync_membership(self):
        """Iterate over all Users and assign Groups using memberOf Field"""
        pass

    def _build_object_properties(self, attributes: Dict[str, Any]) -> Dict[str, Dict[Any, Any]]:
        properties = {
            'attributes': {}
        }
        for mapping in self._source.property_mappings.all().select_subclasses():
            properties[mapping.object_field] = attributes.get(mapping.ldap_property, '')
        if 'objectSid' in attributes:
            properties['attributes']['objectSid'] = attributes.get('objectSid')
        properties['attributes']['distinguishedName'] = attributes.get('distinguishedName')
        return properties

    def auth_user(self, password: str, **filters: Dict[str, str]) -> Optional[User]:
        """Try to bind as either user_dn or mail with password.
        Returns True on success, otherwise False"""
        users = User.objects.filter(**filters)
        if not users.exists():
            return None
        user = users.first()
        if 'distinguishedName' not in user.attributes:
            LOGGER.debug("User doesn't have DN set, assuming not LDAP imported.", user=user)
            return None
        # Try to bind as new user
        LOGGER.debug("Attempting Binding as user", user=user)
        try:
            temp_connection = ldap3.Connection(self._server,
                                               user=user.attributes.get('distinguishedName'),
                                               password=password, raise_exceptions=True)
            temp_connection.bind()
            return user
        except ldap3.core.exceptions.LDAPInvalidCredentialsResult as exception:
            LOGGER.debug("LDAPInvalidCredentialsResult", user=user)
        except ldap3.core.exceptions.LDAPException as exception:
            LOGGER.warning(exception)
        return None
