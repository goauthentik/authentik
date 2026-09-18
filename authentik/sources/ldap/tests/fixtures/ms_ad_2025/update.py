import ssl
from getpass import getpass
from pathlib import Path
from sys import argv

from ldap3 import ALL, ALL_ATTRIBUTES, Connection, Server, Tls

if __name__ == "__main__":
    server = argv[1]
    user = argv[2]
    password = getpass()

    output_dir = Path(__file__).parent

    server = Server(server, get_info=ALL, tls=Tls(validate=ssl.CERT_NONE), use_ssl=True)
    connection = Connection(server, user, password, raise_exceptions=True)
    connection.bind()

    server.info.to_file(str(output_dir / "info.json"))
    server.schema.to_file(str(output_dir / "schema.json"))

    if connection.search(
        server.info.naming_contexts[0], "(objectclass=*)", attributes=ALL_ATTRIBUTES
    ):
        connection.response_to_file(str(output_dir / "entries.json"), raw=True)

    connection.unbind()
