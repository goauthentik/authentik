from hashlib import sha512
from ssl import OPENSSL_VERSION

from cryptography.exceptions import InternalError
from cryptography.hazmat.backends.openssl.backend import backend
from jwcrypto.common import json_encode
from jwcrypto.jwe import JWE
from jwcrypto.jwk import JWK
from jwt import encode
from psutil import cpu_count, virtual_memory

from authentik import get_full_version
from authentik.lib.utils.reflection import get_env
from authentik.root.install_id import get_install_id_raw
from lifecycle.migrate import get_postgres

try:
    backend._enable_fips()
except InternalError:
    pass

def get_version_history():
    with get_postgres() as postgres:
        cur = postgres.cursor()
        cur.execute("""SELECT "timestamp", "version", "build" FROM authentik_version_history;""")
        for x, y, z in cur.fetchall():
            yield (x.timestamp(), y, z)


def generate():
    payload = {
        "version": {
            "history": list(get_version_history()),
            "current": get_full_version(),
        },
        "env": get_env(),
        "install_id_hash": sha512(get_install_id_raw().encode("ascii")).hexdigest()[:16],
        "system": {
            "cpu": {"count": cpu_count()},
            "fips": backend._fips_enabled,
            "ssl": OPENSSL_VERSION,
            "memory_bytes": virtual_memory().total,
        },
    }
    return payload


def encrypt(raw):
    with open("authentik/enterprise/public.pem", "rb") as _key:
        key = JWK.from_pem(_key.read())
    jwe = JWE(
        encode(raw, "foo"),
        json_encode(
            {
                "alg": "ECDH-ES+A256KW",
                "enc": "A256CBC-HS512",
                "typ": "JWE",
            }
        ),
    )
    jwe.add_recipient(key)
    return jwe.serialize(compact=True)


if __name__ == "__main__":
    data = generate()
    snippet = encrypt(data)
    print(f"\n\n\t{data}")
