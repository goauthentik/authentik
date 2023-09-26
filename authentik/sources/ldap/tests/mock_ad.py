"""ldap testing utils"""

from ldap3 import MOCK_SYNC, OFFLINE_AD_2012_R2, Connection, Server

from authentik.sources.ldap.sync.vendor.ms_ad import UserAccountControl


def mock_ad_connection(password: str) -> Connection:
    """Create mock AD connection"""
    server = Server("my_fake_server", get_info=OFFLINE_AD_2012_R2)
    _pass = "foo"  # noqa # nosec
    connection = Connection(
        server,
        user="cn=my_user,dc=goauthentik,dc=io",
        password=_pass,
        client_strategy=MOCK_SYNC,
    )
    # Entry for password checking
    connection.strategy.add_entry(
        "cn=user,ou=users,dc=goauthentik,dc=io",
        {
            "name": "test-user",
            "objectSid": "unique-test-group",
            "objectClass": "person",
            "displayName": "Erin M. Hagens",
            "sAMAccountName": "sAMAccountName",
            "distinguishedName": "cn=user,ou=users,dc=goauthentik,dc=io",
        },
    )
    connection.strategy.add_entry(
        "cn=group1,ou=groups,dc=goauthentik,dc=io",
        {
            "name": "test-group",
            "objectSid": "unique-test-group",
            "objectClass": "group",
            "distinguishedName": "cn=group1,ou=groups,dc=goauthentik,dc=io",
            "member": ["cn=user0,ou=users,dc=goauthentik,dc=io"],
        },
    )
    # Group without SID
    connection.strategy.add_entry(
        "cn=group2,ou=groups,dc=goauthentik,dc=io",
        {
            "name": "test-group",
            "objectClass": "group",
            "distinguishedName": "cn=group2,ou=groups,dc=goauthentik,dc=io",
        },
    )
    connection.strategy.add_entry(
        "cn=user0,ou=users,dc=goauthentik,dc=io",
        {
            "userPassword": password,
            "sAMAccountName": "user0_sn",
            "name": "user0_sn",
            "revision": 0,
            "objectSid": "user0",
            "objectClass": "person",
            "distinguishedName": "cn=user0,ou=foo,ou=users,dc=goauthentik,dc=io",
            "userAccountControl": (
                UserAccountControl.ACCOUNTDISABLE + UserAccountControl.NORMAL_ACCOUNT
            ),
        },
    )
    # User without SID
    connection.strategy.add_entry(
        "cn=user1,ou=users,dc=goauthentik,dc=io",
        {
            "userPassword": "test1111",
            "sAMAccountName": "user2_sn",
            "name": "user1_sn",
            "revision": 0,
            "objectClass": "person",
            "distinguishedName": "cn=user1,ou=users,dc=goauthentik,dc=io",
        },
    )
    # Duplicate users
    connection.strategy.add_entry(
        "cn=user2,ou=users,dc=goauthentik,dc=io",
        {
            "userPassword": "test2222",
            "sAMAccountName": "user2_sn",
            "name": "user2_sn",
            "revision": 0,
            "objectSid": "unique-test2222",
            "objectClass": "person",
            "distinguishedName": "cn=user2,ou=users,dc=goauthentik,dc=io",
        },
    )
    connection.strategy.add_entry(
        "cn=user3,ou=users,dc=goauthentik,dc=io",
        {
            "userPassword": "test2222",
            "sAMAccountName": "user2_sn",
            "name": "user2_sn",
            "revision": 0,
            "objectSid": "unique-test2222",
            "objectClass": "person",
            "distinguishedName": "cn=user3,ou=users,dc=goauthentik,dc=io",
        },
    )
    connection.bind()
    return connection
