"""LDAP Source tests"""
from unittest.mock import PropertyMock, patch

from django.test import TestCase
from ldap3 import MOCK_SYNC, OFFLINE_AD_2012_R2, Connection, Server

from passbook.core.models import User
from passbook.sources.ldap.connector import Connector
from passbook.sources.ldap.models import LDAPPropertyMapping, LDAPSource


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
        "cn=user0,ou=test,o=lab",
        {
            "userPassword": "test0000",
            "sAMAccountName": "user0_sn",
            "revision": 0,
            "objectSid": "unique-test0000",
            "objectCategory": "Person",
        },
    )
    connection.strategy.add_entry(
        "cn=user1,ou=test,o=lab",
        {
            "userPassword": "test1111",
            "sAMAccountName": "user1_sn",
            "revision": 0,
            "objectSid": "unique-test1111",
            "objectCategory": "Person",
        },
    )
    connection.strategy.add_entry(
        "cn=user2,ou=test,o=lab",
        {
            "userPassword": "test2222",
            "sAMAccountName": "user2_sn",
            "revision": 0,
            "objectSid": "unique-test2222",
            "objectCategory": "Person",
        },
    )
    connection.bind()
    return connection


LDAP_CONNECTION_PATCH = PropertyMock(return_value=_build_mock_connection())


class LDAPSourceTests(TestCase):
    """LDAP Source tests"""

    def setUp(self):
        self.source = LDAPSource.objects.create(
            name="ldap", slug="ldap", base_dn="o=lab"
        )
        self.source.property_mappings.set(LDAPPropertyMapping.objects.all())
        self.source.save()

    @patch("passbook.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_sync_users(self):
        """Test user sync"""
        connector = Connector(self.source)
        connector.sync_users()
        user = User.objects.filter(username="user2_sn")
        self.assertTrue(user.exists())
