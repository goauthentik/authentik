"""ldap testing utils"""

from ldap3 import MOCK_SYNC, OFFLINE_SLAPD_2_4, Connection, Server


def mock_slapd_connection(password: str) -> Connection:
    """Create mock AD connection"""
    server = Server("my_fake_server", get_info=OFFLINE_SLAPD_2_4)
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
            "uid": "unique-test-group",
            "objectClass": "person",
            "displayName": "Erin M. Hagens",
        },
    )
    connection.strategy.add_entry(
        "cn=group1,ou=groups,dc=goauthentik,dc=io",
        {
            "name": "test-group",
            "uid": "unique-test-group",
            "objectClass": "group",
            "member": ["cn=user0,ou=users,dc=goauthentik,dc=io"],
        },
    )
    # Group without SID
    connection.strategy.add_entry(
        "cn=group2,ou=groups,dc=goauthentik,dc=io",
        {
            "name": "test-group",
            "objectClass": "group",
        },
    )
    connection.strategy.add_entry(
        "cn=user0,ou=users,dc=goauthentik,dc=io",
        {
            "userPassword": password,
            "name": "user0_sn",
            "uid": "user0_sn",
            "objectClass": "person",
        },
    )
    # User without SID
    connection.strategy.add_entry(
        "cn=user1,ou=users,dc=goauthentik,dc=io",
        {
            "userPassword": "test1111",
            "name": "user1_sn",
            "objectClass": "person",
        },
    )
    # Duplicate users
    connection.strategy.add_entry(
        "cn=user2,ou=users,dc=goauthentik,dc=io",
        {
            "userPassword": "test2222",
            "name": "user2_sn",
            "uid": "unique-test2222",
            "objectClass": "person",
        },
    )
    connection.strategy.add_entry(
        "cn=user3,ou=users,dc=goauthentik,dc=io",
        {
            "userPassword": "test2222",
            "name": "user2_sn",
            "uid": "unique-test2222",
            "objectClass": "person",
        },
    )
    connection.bind()
    return connection
