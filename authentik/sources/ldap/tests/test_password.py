"""LDAP Source tests"""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from authentik.core.models import User
from authentik.sources.ldap.models import LDAPSource, LDAPSourcePropertyMapping
from authentik.sources.ldap.password import LDAPPasswordChanger
from authentik.sources.ldap.tests.mock_ad import mock_ad_connection

LDAP_CONNECTION_PATCH = MagicMock(return_value=mock_ad_connection())


class LDAPPasswordTests(TestCase):
    """LDAP Password tests"""

    def setUp(self):
        self.source = LDAPSource.objects.create(
            name="ldap",
            slug="ldap",
            base_dn="dc=t,dc=goauthentik,dc=io",
            additional_user_dn="",
            additional_group_dn="",
        )
        self.source.user_property_mappings.set(LDAPSourcePropertyMapping.objects.all())
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
            attributes={
                "distinguishedName": "CN=Erin M. Hagens,OU=ak-test,DC=t,DC=goauthentik,DC=io"
            },
        )
        self.assertFalse(pwc.ad_password_complexity("test", user))  # 1 category
        self.assertFalse(pwc.ad_password_complexity("test1", user))  # 2 categories
        self.assertTrue(pwc.ad_password_complexity("test1!", user))  # 2 categories

    @patch("authentik.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_password_complexity_user_name_tokens(self):
        """Test passwords containing display-name tokens"""
        pwc = LDAPPasswordChanger(self.source)
        user = User.objects.create(
            username="test",
            attributes={
                "distinguishedName": "CN=Erin M. Hagens,OU=ak-test,DC=t,DC=goauthentik,DC=io"
            },
        )
        user_attributes = {
            "sAMAccountName": "erin.h",
            "displayName": ["Erin M. Hagens"],
        }
        with patch.object(
            pwc._connection.extend.standard,
            "paged_search",
            return_value=[{"attributes": user_attributes}],
        ):
            self.assertFalse(pwc.ad_password_complexity("ErinA1!", user))
            self.assertFalse(pwc.ad_password_complexity("HagensA1!", user))
            self.assertTrue(pwc.ad_password_complexity("ExampleA1!", user))

    @patch("authentik.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_ad_check_password_existing_sam_account_name(self):
        """Test case-insensitive sAMAccountName containment"""
        pwc = LDAPPasswordChanger(self.source)
        user_attributes = {"sAMAccountName": "account123", "displayName": []}
        with patch.object(
            pwc._connection.extend.standard,
            "paged_search",
            return_value=[{"attributes": user_attributes}],
        ):
            self.assertFalse(pwc._ad_check_password_existing("XXaccount123A1!", "user"))
            self.assertFalse(pwc._ad_check_password_existing("XXAccount123A1!", "user"))
            self.assertTrue(pwc._ad_check_password_existing("XXaccount12A1!", "user"))

    @patch("authentik.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_ad_check_password_existing_display_name_separators(self):
        """Test display-name tokens are split on each documented separator"""
        pwc = LDAPPasswordChanger(self.source)
        for separator in [",", ".", "-", "_", " ", "#", "\t"]:
            with self.subTest(separator=repr(separator)):
                user_attributes = {
                    "sAMAccountName": "account123",
                    "displayName": [f"Erin{separator}Hagens"],
                }
                with patch.object(
                    pwc._connection.extend.standard,
                    "paged_search",
                    return_value=[{"attributes": user_attributes}],
                ):
                    self.assertFalse(pwc._ad_check_password_existing("ErinA1!", "user"))
                    self.assertFalse(pwc._ad_check_password_existing("HagensA1!", "user"))

    @patch("authentik.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_ad_check_password_existing_ignores_short_display_name_tokens(self):
        """Test display-name tokens shorter than three characters are ignored"""
        pwc = LDAPPasswordChanger(self.source)
        user_attributes = {"sAMAccountName": "account123", "displayName": ["AB"]}
        with patch.object(
            pwc._connection.extend.standard,
            "paged_search",
            return_value=[{"attributes": user_attributes}],
        ):
            self.assertTrue(pwc._ad_check_password_existing("AB1!", "user"))
