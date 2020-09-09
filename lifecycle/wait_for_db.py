#!/usr/bin/env python
"""This file needs to be run from the root of the project to correctly
import passbook. This is done by the dockerfile."""
from time import sleep

from psycopg2 import OperationalError, connect
from redis import Redis
from redis.exceptions import RedisError
from structlog import get_logger

from passbook.lib.config import CONFIG

LOGGER = get_logger()

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
        LOGGER.warning("PostgreSQL Connection failed, retrying...")

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
        LOGGER.warning("Redis Connection failed, retrying...")
