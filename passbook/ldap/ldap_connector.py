"""Wrapper for ldap3 to easily manage user"""
import os
import sys
from logging import getLogger
from time import time

import ldap3
import ldap3.core.exceptions

from passbook.core.models import User
from passbook.lib.config import CONFIG

LOGGER = getLogger(__name__)

USERNAME_FIELD = CONFIG.y('ldap.username_field', 'sAMAccountName')
LOGIN_FIELD = CONFIG.y('ldap.login_field', 'userPrincipalName')


class LDAPConnector:
    """Wrapper for ldap3 to easily manage user"""

    con = None
    domain = None
    base_dn = None
    mock = False
    create_users_enabled = False

    def __init__(self, mock=False, con_args=None, server_args=None):
        super().__init__()
        self.create_users_enabled = CONFIG.y('ldap.create_users')

        if not LDAPConnector.enabled:
            LOGGER.debug("LDAP not Enabled")

        if not con_args:
            con_args = {}
        if not server_args:
            server_args = {}
        # Either use mock argument or test is in argv
        self.domain = CONFIG.y('ldap.domain')
        self.base_dn = CONFIG.y('ldap.base_dn')
        if mock or any('test' in arg for arg in sys.argv):
            self.mock = True
            self.create_users_enabled = True
            con_args['client_strategy'] = ldap3.MOCK_SYNC
            server_args['get_info'] = ldap3.OFFLINE_AD_2012_R2

        self.server = ldap3.Server(CONFIG.y('ldap.server.name'), **server_args)
        self.con = ldap3.Connection(self.server, raise_exceptions=True,
                                    user=CONFIG.y('ldap.bind.username'),
                                    password=CONFIG.y('ldap.bind.password'), **con_args)

        if self.mock:
            json_path = os.path.join(os.path.dirname(__file__), 'tests', 'ldap_mock.json')
            self.con.strategy.entries_from_json(json_path)

        self.con.bind()
        if CONFIG.y('ldap.server.use_tls'):
            self.con.start_tls()

    # @staticmethod
    # def cleanup_mock():
    #     """Cleanup mock files which are not this PID's"""
    #     pid = os.getpid()
    #     json_path = os.path.join(os.path.dirname(__file__), 'test', 'ldap_mock_%d.json' % pid)
    #     os.unlink(json_path)
    #     LOGGER.debug("Cleaned up LDAP Mock from PID %d", pid)

    # def apply_db(self):
    #     """Check if any unapplied LDAPModification's are left"""
    #     to_apply = LDAPModification.objects.filter(_purgeable=False)
    #     for obj in to_apply:
    #         try:
    #             if obj.action == LDAPModification.ACTION_ADD:
    #                 self.con.add(obj.dn, obj.data)
    #             elif obj.action == LDAPModification.ACTION_MODIFY:
    #                 self.con.modify(obj.dn, obj.data)

    #             # Object has been successfully applied to LDAP
    #             obj.delete()
    #         except ldap3.core.exceptions.LDAPException as exc:
    #             LOGGER.error(exc)
    #     LOGGER.debug("Recovered %d Modifications from DB.", len(to_apply))

    # @staticmethod
    # def handle_ldap_error(object_dn, action, data):
    #     """Custom Handler for LDAP methods to write LDIF to DB"""
    #     LDAPModification.objects.create(
    #         dn=object_dn,
    #         action=action,
    #         data=data)

    @property
    def enabled(self):
        """Returns whether LDAP is enabled or not"""
        return CONFIG.y('ldap.enabled')

    @staticmethod
    def encode_pass(password):
        """Encodes a plain-text password so it can be used by AD"""
        return '"{}"'.format(password).encode('utf-16-le')

    def lookup(self, generate_only=False, **fields):
        """Search email in LDAP and return the DN.
        Returns False if nothing was found."""
        filters = []
        for item, value in fields.items():
            filters.append("(%s=%s)" % (item, value))
        ldap_filter = "(&%s)" % "".join(filters)
        LOGGER.debug("Constructed filter: '%s'", ldap_filter)
        if generate_only:
            return ldap_filter
        try:
            self.con.search(self.base_dn, ldap_filter)
            results = self.con.response
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
            'username': '%(' + USERNAME_FIELD + ')s',
            'first_name': '%(givenName)s %(sn)s',
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
        if not LDAPConnector.enabled:
            return None
        filters.pop('request')
        # FIXME: Adapt user_uid
        # email = filters.pop(CONFIG.get('passport').get('ldap').get, '')
        email = filters.pop('email')
        user_dn = self.lookup(**{LOGIN_FIELD: email})
        if not user_dn:
            return None
        # Try to bind as new user
        LOGGER.debug("Binding as '%s'", user_dn)
        try:
            t_con = ldap3.Connection(self.server, user=user_dn,
                                     password=password, raise_exceptions=True)
            t_con.bind()
            if self.con.search(
                    search_base=self.base_dn,
                    search_filter=self.lookup(generate_only=True, **{LOGIN_FIELD: email}),
                    search_scope=ldap3.SUBTREE,
                    attributes=[ldap3.ALL_ATTRIBUTES, ldap3.ALL_OPERATIONAL_ATTRIBUTES],
                    get_operational_attributes=True,
                    size_limit=1,
            ):
                response = self.con.response[0]
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

    def is_email_used(self, mail):
        """Checks whether an email address is already registered in LDAP"""
        if self.create_users_enabled:
            return self.lookup(mail=mail)
        return False

    def create_ldap_user(self, user, raw_password):
        """Creates a new LDAP User from a django user and raw_password.
        Returns True on success, otherwise False"""
        if not self.create_users_enabled:
            LOGGER.debug("User creation not enabled")
            return False
        # The dn of our new entry/object
        username = user.pk.hex # UUID without dashes
        # sAMAccountName is limited to 20 chars
        # https://msdn.microsoft.com/en-us/library/ms679635.aspx
        username_trunk = username[:20] if len(username) > 20 else username
        # AD doesn't like sAMAccountName's with . at the end
        username_trunk = username_trunk[:-1] if username_trunk[-1] == '.' else username_trunk
        user_dn = 'cn=' + username + ',' + self.base_dn
        LOGGER.debug('New DN: %s', user_dn)
        attrs = {
            'distinguishedName': str(user_dn),
            'cn': str(username),
            'description': str('t=' + time()),
            'sAMAccountName': str(username_trunk),
            'givenName': str(user.first_name),
            'displayName': str(user.username),
            'name': str(user.first_name),
            'mail': str(user.email),
            'userPrincipalName': str(username + '@' + self.domain),
            'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
        }
        try:
            self.con.add(user_dn, attributes=attrs)
        except ldap3.core.exceptions.LDAPException as exception:
            LOGGER.warning("Failed to create user ('%s'), saved to DB", exception)
            # LDAPConnector.handle_ldap_error(user_dn, LDAPModification.ACTION_ADD, attrs)
        LOGGER.debug("Signed up user %s", user.email)
        return self.change_password(raw_password, mail=user.email)

    def _do_modify(self, diff, **fields):
        """Do the LDAP modification itself"""
        user_dn = self.lookup(**fields)
        try:
            self.con.modify(user_dn, diff)
        except ldap3.core.exceptions.LDAPException as exception:
            LOGGER.warning("Failed to modify %s ('%s'), saved to DB", user_dn, exception)
            # LDAPConnector.handle_ldap_error(user_dn, LDAPModification.ACTION_MODIFY, diff)
        LOGGER.debug("modified account '%s' [%s]", user_dn, ','.join(diff.keys()))
        return 'result' in self.con.result and self.con.result['result'] == 0

    def disable_user(self, **fields):
        """
        Disables LDAP user based on mail or user_dn.
        Returns True on success, otherwise False
        """
        diff = {
            'userAccountControl': [(ldap3.MODIFY_REPLACE, [str(66050)])],
        }
        return self._do_modify(diff, **fields)

    def enable_user(self, **fields):
        """
        Enables LDAP user based on mail or user_dn.
        Returns True on success, otherwise False
        """
        diff = {
            'userAccountControl': [(ldap3.MODIFY_REPLACE, [str(66048)])],
        }
        return self._do_modify(diff, **fields)

    def change_password(self, new_password, **fields):
        """
        Changes LDAP user's password based on mail or user_dn.
        Returns True on success, otherwise False
        """
        diff = {
            'unicodePwd': [(ldap3.MODIFY_REPLACE, [LDAPConnector.encode_pass(new_password)])],
        }
        return self._do_modify(diff, **fields)

    def add_to_group(self, group_dn, **fields):
        """
        Adds mail or user_dn to group_dn
        Returns True on success, otherwise False
        """
        user_dn = self.lookup(**fields)
        diff = {
            'member': [(ldap3.MODIFY_ADD), [user_dn]]
        }
        return self._do_modify(diff, user_dn=group_dn)

    def remove_from_group(self, group_dn, **fields):
        """
        Removes mail or user_dn from group_dn
        Returns True on success, otherwise False
        """
        user_dn = self.lookup(**fields)
        diff = {
            'member': [(ldap3.MODIFY_DELETE), [user_dn]]
        }
        return self._do_modify(diff, user_dn=group_dn)
