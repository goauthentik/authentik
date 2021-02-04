"""ldap testing utils"""

from ldap3 import MOCK_SYNC, OFFLINE_AD_2012_R2, Connection, Server


def mock_ad_connection(password: str) -> Connection:
    """Create mock AD connection"""
    server = Server("my_fake_server", get_info=OFFLINE_AD_2012_R2)
    _pass = "foo"  # noqa # nosec
    connection = Connection(
        server,
        user="cn=my_user,DC=AD2012,DC=LAB",
        password=_pass,
        client_strategy=MOCK_SYNC,
    )
    # Entry for password checking
    connection.strategy.add_entry(
        "cn=user,ou=users,DC=AD2012,DC=LAB",
        {
            "name": "test-user",
            "objectSid": "unique-test-group",
            "objectCategory": "Person",
            "displayName": "Erin M. Hagens",
            "sAMAccountName": "sAMAccountName",
            "distinguishedName": "cn=user,ou=users,DC=AD2012,DC=LAB",
        },
    )
    connection.strategy.add_entry(
        "cn=group1,ou=groups,DC=AD2012,DC=LAB",
        {
            "name": "test-group",
            "objectSid": "unique-test-group",
            "objectCategory": "Group",
            "distinguishedName": "cn=group1,ou=groups,DC=AD2012,DC=LAB",
            "member": ["cn=user0,ou=users,DC=AD2012,DC=LAB"],
        },
    )
    # Group without SID
    connection.strategy.add_entry(
        "cn=group2,ou=groups,DC=AD2012,DC=LAB",
        {
            "name": "test-group",
            "objectCategory": "Group",
            "distinguishedName": "cn=group2,ou=groups,DC=AD2012,DC=LAB",
        },
    )
    connection.strategy.add_entry(
        "cn=user0,ou=users,DC=AD2012,DC=LAB",
        {
            "userPassword": password,
            "sAMAccountName": "user0_sn",
            "name": "user0_sn",
            "revision": 0,
            "objectSid": "user0",
            "objectCategory": "Person",
            "distinguishedName": "cn=user0,ou=users,DC=AD2012,DC=LAB",
        },
    )
    # User without SID
    connection.strategy.add_entry(
        "cn=user1,ou=users,DC=AD2012,DC=LAB",
        {
            "userPassword": "test1111",
            "sAMAccountName": "user2_sn",
            "name": "user1_sn",
            "revision": 0,
            "objectCategory": "Person",
            "distinguishedName": "cn=user1,ou=users,DC=AD2012,DC=LAB",
        },
    )
    # Duplicate users
    connection.strategy.add_entry(
        "cn=user2,ou=users,DC=AD2012,DC=LAB",
        {
            "userPassword": "test2222",
            "sAMAccountName": "user2_sn",
            "name": "user2_sn",
            "revision": 0,
            "objectSid": "unique-test2222",
            "objectCategory": "Person",
            "distinguishedName": "cn=user2,ou=users,DC=AD2012,DC=LAB",
        },
    )
    connection.strategy.add_entry(
        "cn=user3,ou=users,DC=AD2012,DC=LAB",
        {
            "userPassword": "test2222",
            "sAMAccountName": "user2_sn",
            "name": "user2_sn",
            "revision": 0,
            "objectSid": "unique-test2222",
            "objectCategory": "Person",
            "distinguishedName": "cn=user3,ou=users,DC=AD2012,DC=LAB",
        },
    )
    connection.bind()
    return connection
