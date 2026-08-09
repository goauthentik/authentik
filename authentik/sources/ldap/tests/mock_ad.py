"""ldap testing utils"""

from ldap3 import MOCK_SYNC, Connection, Server
from ldap3.strategy.mockSync import MockSyncStrategy

from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture


def mock_ad_connection() -> Connection:
    """Create mock AD connection"""
    server = Server.from_definition(
        "my_fake_server",
        dsa_info=load_fixture("fixtures/ms_ad_2025/info.json"),
        dsa_schema=load_fixture("fixtures/ms_ad_2025/schema.json"),
    )
    connection = Connection(
        server,
        user="cn=ak-service-account,dc=t,dc=goauthentik,dc=io",
        password=generate_id(),
        client_strategy=MOCK_SYNC,
    )
    strategy: MockSyncStrategy = connection.strategy
    strategy.entries_from_json(load_fixture("fixtures/ms_ad_2025/entries.json", path_only=True))
    connection.bind()
    return connection
