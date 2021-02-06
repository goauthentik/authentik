"""LDAP Source managed objects"""
from authentik.managed.manager import EnsureExists, ObjectManager
from authentik.sources.ldap.models import LDAPPropertyMapping


class LDAPProviderManager(ObjectManager):
    """LDAP Source managed objects"""

    def reconcile(self):
        return [
            EnsureExists(
                LDAPPropertyMapping,
                "goauthentik.io/sources/ldap/default-name",
                name="authentik default LDAP Mapping: Name",
                object_field="name",
                expression="return ldap.get('name')",
            ),
            EnsureExists(
                LDAPPropertyMapping,
                "goauthentik.io/sources/ldap/default-mail",
                name="authentik default LDAP Mapping: mail",
                object_field="email",
                expression="return ldap.get('mail')",
            ),
            # Active Directory-specific mappings
            EnsureExists(
                LDAPPropertyMapping,
                "goauthentik.io/sources/ldap/ms-samaccountname",
                name="authentik default Active Directory Mapping: sAMAccountName",
                object_field="username",
                expression="return ldap.get('sAMAccountName')",
            ),
            EnsureExists(
                LDAPPropertyMapping,
                "goauthentik.io/sources/ldap/ms-userprincipalname",
                name="authentik default Active Directory Mapping: userPrincipalName",
                object_field="attributes.upn",
                expression="return ldap.get('userPrincipalName')",
            ),
            EnsureExists(
                LDAPPropertyMapping,
                "goauthentik.io/sources/ldap/ms-givenName",
                name="authentik default Active Directory Mapping: givenName",
                object_field="attributes.givenName",
                expression="return ldap.get('givenName')",
            ),
            EnsureExists(
                LDAPPropertyMapping,
                "goauthentik.io/sources/ldap/ms-sn",
                name="authentik default Active Directory Mapping: sn",
                object_field="attributes.sn",
                expression="return ldap.get('sn')",
            ),
            # OpenLDAP specific mappings
            EnsureExists(
                LDAPPropertyMapping,
                "goauthentik.io/sources/ldap/openldap-uid",
                name="authentik default OpenLDAP Mapping: uid",
                object_field="username",
                expression="return ldap.get('uid')",
            ),
            EnsureExists(
                LDAPPropertyMapping,
                "goauthentik.io/sources/ldap/openldap-cn",
                name="authentik default OpenLDAP Mapping: cn",
                object_field="name",
                expression="return ldap.get('cn')",
            ),
        ]
