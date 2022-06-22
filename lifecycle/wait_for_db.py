#!/usr/bin/env python
"""This file needs to be run from the root of the project to correctly
import authentik. This is done by the dockerfile."""
from json import dumps
from sys import exit as sysexit
from sys import stderr
from time import sleep, time
from urllib.parse import quote_plus

from psycopg2 import OperationalError, connect
from redis import Redis
from redis.exceptions import RedisError

from authentik.lib.config import CONFIG


def j_print(event: str, log_level: str = "info", **kwargs):
    """Print event in the same format as structlog with JSON.
    Used before structlog is configured."""
    data = {
        "event": event,
        "level": log_level,
        "logger": __name__,
        "timestamp": time(),
    }
    data.update(**kwargs)
    print(dumps(data), file=stderr)


j_print("Starting authentik bootstrap")

# Sanity check, ensure SECRET_KEY is set before we even check for database connectivity
if CONFIG.y("secret_key") is None or len(CONFIG.y("secret_key")) == 0:
    j_print("----------------------------------------------------------------------")
    j_print("Secret key missing, check https://goauthentik.io/docs/installation/.")
    j_print("----------------------------------------------------------------------")
    sysexit(1)


while True:
    try:
        conn = connect(
            dbname=CONFIG.y("postgresql.name"),
            user=CONFIG.y("postgresql.user"),
            password=CONFIG.y("postgresql.password"),
            host=CONFIG.y("postgresql.host"),
            port=int(CONFIG.y("postgresql.port")),
        )
        conn.cursor()
        break
    except OperationalError as exc:
        sleep(1)
        j_print(f"PostgreSQL connection failed, retrying... ({exc})")
    j_print("PostgreSQL connection successful")

REDIS_PROTOCOL_PREFIX = "redis://"
if CONFIG.y_bool("redis.tls", False):
    REDIS_PROTOCOL_PREFIX = "rediss://"
REDIS_URL = (
    f"{REDIS_PROTOCOL_PREFIX}:"
    f"{quote_plus(CONFIG.y('redis.password'))}@{quote_plus(CONFIG.y('redis.host'))}:"
    f"{int(CONFIG.y('redis.port'))}/{CONFIG.y('redis.ws_db')}"
)
while True:
    try:
        redis = Redis.from_url(REDIS_URL)
        redis.ping()
        break
    except RedisError as exc:
        sleep(1)
        j_print(f"Redis Connection failed, retrying... ({exc})", redis_url=REDIS_URL)
    j_print("Redis Connection successful")

j_print("Finished authentik bootstrap")
