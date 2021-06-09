#!/usr/bin/env python
"""This file needs to be run from the root of the project to correctly
import authentik. This is done by the dockerfile."""
from json import dumps
from sys import stderr
from time import sleep, time

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
        j_print(f"PostgreSQL Connection failed, retrying... ({exc})")

while True:
    try:
        redis = Redis.from_url(
            f"redis://:{CONFIG.y('redis.password')}@{CONFIG.y('redis.host')}:6379"
            f"/{CONFIG.y('redis.ws_db')}"
        )
        redis.ping()
        break
    except RedisError as exc:
        sleep(1)
        j_print(f"Redis Connection failed, retrying... ({exc})")
