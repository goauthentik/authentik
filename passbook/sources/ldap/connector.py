"""Wrapper for ldap3 to easily manage user"""
from time import time

import ldap3
import ldap3.core.exceptions
from structlog import get_logger

from passbook.core.models import User
from passbook.lib.config import CONFIG
from passbook.sources.ldap.models import LDAPSource

LOGGER = get_logger()

# USERNAME_FIELD = CONFIG.y('ldap.username_field', 'sAMAccountName')
# LOGIN_FIELD = CONFIG.y('ldap.login_field', 'userPrincipalName')


class Connector:
    """Wrapper for ldap3 to easily manage user authentication and creation"""

    _server: ldap3.Server
    _connection = ldap3.Connection
    _source: LDAPSource

    def __init__(self, source: LDAPSource):
        self._source = source

        if not self._source.enabled:
            LOGGER.debug("LDAP not Enabled")

        self._server = ldap3.Server(source.server_uri) # Implement URI parsing
        self._connection = ldap3.Connection(self._server, raise_exceptions=True,
                                            user=source.bind_cn,
                                            password=source.bind_password)

        self._connection.bind()
        if source.start_tls:
            self._connection.start_tls()

    @staticmethod
    def encode_pass(password: str) -> str:
        """Encodes a plain-text password so it can be used by AD"""
        return '"{}"'.format(password).encode('utf-16-le')

    def generate_filter(self, **fields):
        """Generate LDAP filter from **fields."""
        filters = []
        for item, value in fields.items():
            filters.append("(%s=%s)" % (item, value))
        ldap_filter = "(&%s)" % "".join(filters)
        LOGGER.debug("Constructed filter: '%s'", ldap_filter)
        return ldap_filter

    def lookup(self, ldap_filter: str):
        """Search email in LDAP and return the DN.
        Returns False if nothing was found."""
        try:
            self._connection.search(self._source.search_base, ldap_filter)
            results = self._connection.response
            if len(results) >= 1:
                if 'dn' in results[0]:
                    return str(results[0]['dn'])
        except ldap3.core.exceptions.LDAPNoSuchObjectResult as exc:
            LOGGER.warning(exc)
            return False
        except ldap3.core.exceptions.LDAPInvalidDnError as exc:
            LOGGER.warning(exc)
            return False
        return False

    def _get_or_create_user(self, user_data):
        """Returns a Django user for the given LDAP user data.
        If the user does not exist, then it will be created."""
        attributes = user_data.get("attributes")
        if attributes is None:
            LOGGER.warning("LDAP user attributes empty")
            return None
        # Create the user data.
        field_map = {
            'username': '%(' + ')s',
            'name': '%(givenName)s %(sn)s',
            'email': '%(mail)s',
        }
        user_fields = {}
        for dj_field, ldap_field in field_map.items():
            user_fields[dj_field] = ldap_field % attributes

        # Update or create the user.
        user, created = User.objects.update_or_create(
            defaults=user_fields,
            username=user_fields.pop('username', "")
        )

        # Update groups
        # if 'memberOf' in attributes:
        #     applicable_groups = LDAPGroupMapping.objects.f
        # ilter(ldap_dn__in=attributes['memberOf'])
        #     for group in applicable_groups:
        #         if group.group not in user.groups.all():
        #             user.groups.add(group.group)
        #             user.save()

        # If the user was created, set them an unusable password.
        if created:
            user.set_unusable_password()
            user.save()
        # All done!
        LOGGER.debug("LDAP user lookup succeeded")
        return user

    def auth_user(self, password, **filters):
        """Try to bind as either user_dn or mail with password.
        Returns True on success, otherwise False"""
        filters.pop('request')
        if not self._source.enabled:
            return None
        # FIXME: Adapt user_uid
        # email = filters.pop(CONFIG.y('passport').get('ldap').get, '')
        email = filters.pop('email')
        user_dn = self.lookup(self.generate_filter(**{'email': email}))
        if not user_dn:
            return None
        # Try to bind as new user
        LOGGER.debug("Binding as '%s'", user_dn)
        try:
            temp_connection = ldap3.Connection(self._server, user=user_dn,
                                               password=password, raise_exceptions=True)
            temp_connection.bind()
            if self._connection.search(
                    search_base=self._source.search_base,
                    search_filter=self.generate_filter(**{'email': email}),
                    search_scope=ldap3.SUBTREE,
                    attributes=[ldap3.ALL_ATTRIBUTES, ldap3.ALL_OPERATIONAL_ATTRIBUTES],
                    get_operational_attributes=True,
                    size_limit=1,
            ):
                response = self._connection.response[0]
                # If user has no email set in AD, use UPN
                if 'mail' not in response.get('attributes'):
                    response['attributes']['mail'] = response['attributes']['userPrincipalName']
                return self._get_or_create_user(response)
            LOGGER.warning("LDAP user lookup failed")
            return None
        except ldap3.core.exceptions.LDAPInvalidCredentialsResult as exception:
            LOGGER.debug("User '%s' failed to login (Wrong credentials)", user_dn)
        except ldap3.core.exceptions.LDAPException as exception:
            LOGGER.warning(exception)
        return None

    def _do_modify(self, diff, **fields):
        """Do the LDAP modification itself"""
        user_dn = self.lookup(self.generate_filter(**fields))
        try:
            self._connection.modify(user_dn, diff)
        except ldap3.core.exceptions.LDAPException as exception:
            LOGGER.warning("Failed to modify %s ('%s'), saved to DB", user_dn, exception)
            # Connector.handle_ldap_error(user_dn, LDAPModification.ACTION_MODIFY, diff)
        LOGGER.debug("modified account '%s' [%s]", user_dn, ','.join(diff.keys()))
        return 'result' in self._connection.result and self._connection.result['result'] == 0

    def disable_user(self, **fields):
        """Disables LDAP user based on mail or user_dn.
        Returns True on success, otherwise False"""
        diff = {
            'userAccountControl': [(ldap3.MODIFY_REPLACE, [str(66050)])],
        }
        return self._do_modify(diff, **fields)

    def enable_user(self, **fields):
        """Enables LDAP user based on mail or user_dn.
        Returns True on success, otherwise False"""
        diff = {
            'userAccountControl': [(ldap3.MODIFY_REPLACE, [str(66048)])],
        }
        return self._do_modify(diff, **fields)

    def change_password(self, new_password, **fields):
        """Changes LDAP user's password based on mail or user_dn.
        Returns True on success, otherwise False"""
        diff = {
            'unicodePwd': [(ldap3.MODIFY_REPLACE, [Connector.encode_pass(new_password)])],
        }
        return self._do_modify(diff, **fields)

    def add_to_group(self, group_dn, **fields):
        """Adds mail or user_dn to group_dn
        Returns True on success, otherwise False"""
        user_dn = self.lookup(**fields)
        diff = {
            'member': [(ldap3.MODIFY_ADD), [user_dn]]
        }
        return self._do_modify(diff, user_dn=group_dn)

    def remove_from_group(self, group_dn, **fields):
        """Removes mail or user_dn from group_dn
        Returns True on success, otherwise False"""
        user_dn = self.lookup(**fields)
        diff = {
            'member': [(ldap3.MODIFY_DELETE), [user_dn]]
        }
        return self._do_modify(diff, user_dn=group_dn)
