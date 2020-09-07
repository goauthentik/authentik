"""LDAP Source tests"""
from unittest.mock import Mock, PropertyMock, patch

from django.test import TestCase
from ldap3 import MOCK_SYNC, OFFLINE_AD_2012_R2, Connection, Server

from passbook.core.models import Group, User
from passbook.providers.oauth2.generators import generate_client_secret
from passbook.sources.ldap.auth import LDAPBackend
from passbook.sources.ldap.connector import Connector
from passbook.sources.ldap.models import LDAPPropertyMapping, LDAPSource
from passbook.sources.ldap.tasks import sync


def _build_mock_connection() -> Connection:
    """Create mock connection"""
    server = Server("my_fake_server", get_info=OFFLINE_AD_2012_R2)
    _pass = "foo"  # noqa # nosec
    connection = Connection(
        server,
        user="cn=my_user,ou=test,o=lab",
        password=_pass,
        client_strategy=MOCK_SYNC,
    )
    connection.strategy.add_entry(
        "cn=group1,ou=groups,ou=test,o=lab",
        {
            "name": "test-group",
            "objectSid": "unique-test-group",
            "objectCategory": "Group",
            "distinguishedName": "cn=group1,ou=groups,ou=test,o=lab",
        },
    )
    # Group without SID
    connection.strategy.add_entry(
        "cn=group2,ou=groups,ou=test,o=lab",
        {
            "name": "test-group",
            "objectCategory": "Group",
            "distinguishedName": "cn=group2,ou=groups,ou=test,o=lab",
        },
    )
    connection.strategy.add_entry(
        "cn=user0,ou=users,ou=test,o=lab",
        {
            "userPassword": LDAP_PASSWORD,
            "sAMAccountName": "user0_sn",
            "name": "user0_sn",
            "revision": 0,
            "objectSid": "user0",
            "objectCategory": "Person",
            "memberOf": "cn=group1,ou=groups,ou=test,o=lab",
        },
    )
    # User without SID
    connection.strategy.add_entry(
        "cn=user1,ou=users,ou=test,o=lab",
        {
            "userPassword": "test1111",
            "sAMAccountName": "user2_sn",
            "name": "user1_sn",
            "revision": 0,
            "objectCategory": "Person",
        },
    )
    # Duplicate users
    connection.strategy.add_entry(
        "cn=user2,ou=users,ou=test,o=lab",
        {
            "userPassword": "test2222",
            "sAMAccountName": "user2_sn",
            "name": "user2_sn",
            "revision": 0,
            "objectSid": "unique-test2222",
            "objectCategory": "Person",
        },
    )
    connection.strategy.add_entry(
        "cn=user3,ou=users,ou=test,o=lab",
        {
            "userPassword": "test2222",
            "sAMAccountName": "user2_sn",
            "name": "user2_sn",
            "revision": 0,
            "objectSid": "unique-test2222",
            "objectCategory": "Person",
        },
    )
    connection.bind()
    return connection


LDAP_PASSWORD = generate_client_secret()
LDAP_CONNECTION_PATCH = PropertyMock(return_value=_build_mock_connection())


class LDAPSourceTests(TestCase):
    """LDAP Source tests"""

    def setUp(self):
        self.source = LDAPSource.objects.create(
            name="ldap",
            slug="ldap",
            base_dn="ou=test,o=lab",
            additional_user_dn="ou=users",
            additional_group_dn="ou=groups",
        )
        self.source.property_mappings.set(LDAPPropertyMapping.objects.all())
        self.source.save()

    @patch("passbook.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_sync_users(self):
        """Test user sync"""
        connector = Connector(self.source)
        connector.sync_users()
        self.assertTrue(User.objects.filter(username="user0_sn").exists())
        self.assertFalse(User.objects.filter(username="user1_sn").exists())

    @patch("passbook.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_sync_groups(self):
        """Test group sync"""
        connector = Connector(self.source)
        connector.sync_groups()
        connector.sync_membership()
        group = Group.objects.filter(name="test-group")
        self.assertTrue(group.exists())

    @patch("passbook.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_auth(self):
        """Test Cached auth"""
        connector = Connector(self.source)
        connector.sync_users()

        user = User.objects.get(username="user0_sn")
        auth_user_by_bind = Mock(return_value=user)
        with patch(
            "passbook.sources.ldap.connector.Connector.auth_user_by_bind",
            auth_user_by_bind,
        ):
            backend = LDAPBackend()
            self.assertEqual(
                backend.authenticate(None, username="user0_sn", password=LDAP_PASSWORD),
                user,
            )

    @patch("passbook.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_tasks(self):
        """Test Scheduled tasks"""
        sync()
