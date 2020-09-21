"""LDAP Source tests"""
from unittest.mock import PropertyMock, patch

from django.test import TestCase

from passbook.core.models import User
from passbook.providers.oauth2.generators import generate_client_secret
from passbook.sources.ldap.models import LDAPPropertyMapping, LDAPSource
from passbook.sources.ldap.password import LDAPPasswordChanger
from passbook.sources.ldap.tests.utils import _build_mock_connection

LDAP_PASSWORD = generate_client_secret()
LDAP_CONNECTION_PATCH = PropertyMock(return_value=_build_mock_connection(LDAP_PASSWORD))


class LDAPPasswordTests(TestCase):
    """LDAP Password tests"""

    def setUp(self):
        self.source = LDAPSource.objects.create(
            name="ldap",
            slug="ldap",
            base_dn="DC=AD2012,DC=LAB",
            additional_user_dn="ou=users",
            additional_group_dn="ou=groups",
        )
        self.source.property_mappings.set(LDAPPropertyMapping.objects.all())
        self.source.save()

    @patch("passbook.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_password_complexity(self):
        """Test password without user"""
        pwc = LDAPPasswordChanger(self.source)
        self.assertFalse(pwc.ad_password_complexity("test"))  # 1 category
        self.assertFalse(pwc.ad_password_complexity("test1"))  # 2 categories
        self.assertTrue(pwc.ad_password_complexity("test1!"))  # 2 categories

    @patch("passbook.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_password_complexity_user(self):
        """test password with user"""
        pwc = LDAPPasswordChanger(self.source)
        user = User.objects.create(
            username="test",
            attributes={"distinguishedName": "cn=user,ou=users,DC=AD2012,DC=LAB"},
        )
        self.assertFalse(pwc.ad_password_complexity("test", user))  # 1 category
        self.assertFalse(pwc.ad_password_complexity("test1", user))  # 2 categories
        self.assertTrue(pwc.ad_password_complexity("test1!", user))  # 2 categories
        self.assertFalse(
            pwc.ad_password_complexity("erin!qewrqewr", user)
        )  # displayName token
        self.assertFalse(
            pwc.ad_password_complexity("hagens!qewrqewr", user)
        )  # displayName token
