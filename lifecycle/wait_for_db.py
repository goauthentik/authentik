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
        )
        conn.cursor()
        break
    except OperationalError:
        sleep(1)
        j_print("PostgreSQL Connection failed, retrying...")

while True:
    try:
        redis = Redis(
            host=CONFIG.y("redis.host"),
            port=6379,
            db=CONFIG.y("redis.message_queue_db"),
            password=CONFIG.y("redis.password"),
        )
        redis.ping()
        break
    except RedisError:
        sleep(1)
        j_print("Redis Connection failed, retrying...")
