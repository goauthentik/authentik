"""LDAP Source tests"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from authentik.core.models import User
from authentik.lib.generators import generate_key
from authentik.sources.ldap.models import LDAPPropertyMapping, LDAPSource
from authentik.sources.ldap.password import LDAPPasswordChanger
from authentik.sources.ldap.tests.mock_ad import mock_ad_connection

LDAP_PASSWORD = generate_key()
LDAP_CONNECTION_PATCH = MagicMock(return_value=mock_ad_connection(LDAP_PASSWORD))


class LDAPPasswordTests(TestCase):
    """LDAP Password tests"""

    def setUp(self):
        self.source = LDAPSource.objects.create(
            name="ldap",
            slug="ldap",
            base_dn="dc=goauthentik,dc=io",
            additional_user_dn="ou=users",
            additional_group_dn="ou=groups",
        )
        self.source.property_mappings.set(LDAPPropertyMapping.objects.all())
        self.source.save()

    @patch("authentik.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_password_complexity(self):
        """Test password without user"""
        pwc = LDAPPasswordChanger(self.source)
        self.assertFalse(pwc.ad_password_complexity("test"))  # 1 category
        self.assertFalse(pwc.ad_password_complexity("test1"))  # 2 categories
        self.assertTrue(pwc.ad_password_complexity("test1!"))  # 2 categories

    @patch("authentik.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_password_complexity_user(self):
        """test password with user"""
        pwc = LDAPPasswordChanger(self.source)
        user = User.objects.create(
            username="test",
            attributes={"distinguishedName": "cn=user,ou=users,dc=goauthentik,dc=io"},
        )
        self.assertFalse(pwc.ad_password_complexity("test", user))  # 1 category
        self.assertFalse(pwc.ad_password_complexity("test1", user))  # 2 categories
        self.assertTrue(pwc.ad_password_complexity("test1!", user))  # 2 categories
        self.assertFalse(pwc.ad_password_complexity("erin!qewrqewr", user))  # displayName token
        self.assertFalse(pwc.ad_password_complexity("hagens!qewrqewr", user))  # displayName token
