"""ldap testing utils"""

from ldap3 import MOCK_SYNC, OFFLINE_DS389_1_3_3, Connection, Server


def mock_freeipa_connection(password: str) -> Connection:
    """Create mock FreeIPA-ish connection"""
    server = Server("my_fake_server", get_info=OFFLINE_DS389_1_3_3)
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
            "cn": "group1",
            "uid": "unique-test-group",
            "objectClass": "groupOfNames",
            "member": ["cn=user0,ou=users,dc=goauthentik,dc=io"],
        },
    )
    # Group without SID
    connection.strategy.add_entry(
        "cn=group2,ou=groups,dc=goauthentik,dc=io",
        {
            "cn": "group2",
            "objectClass": "groupOfNames",
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
    # Group with posixGroup and memberUid
    connection.strategy.add_entry(
        "cn=group-posix,ou=groups,dc=goauthentik,dc=io",
        {
            "cn": "group-posix",
            "objectClass": "posixGroup",
            "memberUid": ["user-posix"],
        },
    )
    # User with posixAccount
    connection.strategy.add_entry(
        "cn=user-posix,ou=users,dc=goauthentik,dc=io",
        {
            "userPassword": password,
            "uid": "user-posix",
            "cn": "user-posix",
            "objectClass": "posixAccount",
        },
    )
    # Locked out user
    connection.strategy.add_entry(
        "cn=user-nsaccountlock,ou=users,dc=goauthentik,dc=io",
        {
            "userPassword": password,
            "uid": "user-nsaccountlock",
            "cn": "user-nsaccountlock",
            "objectClass": "person",
            "nsaccountlock": ["TRUE"],
        },
    )
    connection.bind()
    return connection
