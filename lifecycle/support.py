import platform
from hashlib import sha512
from pprint import pprint
from ssl import OPENSSL_VERSION
from sys import version as python_version

from cryptography.exceptions import InternalError
from cryptography.hazmat.backends.openssl.backend import backend
from jwcrypto.common import json_encode
from jwcrypto.jwe import JWE
from jwcrypto.jwk import JWK
from jwt import encode
from psutil import cpu_count, virtual_memory
from redis import Redis

from authentik import get_full_version
from authentik.lib.config import CONFIG
from authentik.lib.utils.reflection import get_env
from authentik.root.install_id import get_install_id_raw
from lifecycle.wait_for_db import get_postgres, get_redis

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


def get_postgres_version():
    with get_postgres() as postgres:
        cur = postgres.cursor()
        cur.execute("""SELECT version();""")
        return cur.fetchone()[0]


def get_redis_version():
    redis: Redis = get_redis()
    version = redis.info()
    redis.close()
    return f"{version["redis_version"]} {version["redis_mode"]} {version["os"]}"


def get_limited_config():
    return {
        "postgresql": {
            "host": CONFIG.get("postgresql.host"),
        },
        "redis": {
            "host": CONFIG.get("redis.host"),
        },
        "debug": CONFIG.get_bool("debug"),
        "log_level": CONFIG.get("log_level"),
        "error_reporting": {
            "enabled": CONFIG.get_bool("error_reporting.enabled"),
        },
    }


def generate():
    payload = {
        "version": {
            "history": list(get_version_history()),
            "current": get_full_version(),
            "postgres": get_postgres_version(),
            "redis": get_redis_version(),
            "ssl": OPENSSL_VERSION,
            "python": python_version,
        },
        "env": get_env(),
        "install_id_hash": sha512(get_install_id_raw().encode("ascii")).hexdigest()[:16],
        "system": {
            "cpu": {"count": cpu_count()},
            "fips": backend._fips_enabled,
            "memory_bytes": virtual_memory().total,
            "architecture": platform.machine(),
            "platform": platform.platform(),
            "uname": " ".join(platform.uname()),
        },
        "config": get_limited_config(),
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
    pprint(data)
