"""ldap testing utils"""

from ldap3 import MOCK_SYNC, OFFLINE_SLAPD_2_4, Connection, Server

# The mock modifies these in place, so we have to define them per string
user_in_slapd_dn = "cn=user_in_slapd_cn,ou=users,dc=goauthentik,dc=io"
user_in_slapd_cn = "user_in_slapd_cn"
user_in_slapd_uid = "user_in_slapd_uid"
user_in_slapd_object_class = "person"
user_in_slapd = {
    "dn": user_in_slapd_dn,
    "attributes": {
        "cn": user_in_slapd_cn,
        "uid": user_in_slapd_uid,
        "objectClass": user_in_slapd_object_class,
    },
}
group_in_slapd_dn = "cn=user_in_slapd_cn,ou=groups,dc=goauthentik,dc=io"
group_in_slapd_cn = "group_in_slapd_cn"
group_in_slapd_uid = "group_in_slapd_uid"
group_in_slapd_object_class = "groupOfNames"
group_in_slapd = {
    "dn": group_in_slapd_dn,
    "attributes": {
        "cn": group_in_slapd_cn,
        "uid": group_in_slapd_uid,
        "objectClass": group_in_slapd_object_class,
        "member": [user_in_slapd["dn"]],
    },
}


def mock_slapd_connection(password: str) -> Connection:
    """Create mock SLAPD connection"""
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
    # Known user and group
    connection.strategy.add_entry(
        user_in_slapd["dn"],
        user_in_slapd["attributes"],
    )
    connection.strategy.add_entry(
        group_in_slapd["dn"],
        group_in_slapd["attributes"],
    )
    connection.bind()
    return connection
