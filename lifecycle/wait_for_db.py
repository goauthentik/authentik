#!/usr/bin/env python
"""This file needs to be run from the root of the project to correctly
import authentik. This is done by the dockerfile."""
from sys import exit as sysexit
from time import sleep
from urllib.parse import quote_plus

from psycopg import OperationalError, connect
from redis import Redis
from redis.exceptions import RedisError
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()

LOGGER.info("Starting authentik bootstrap")

# Sanity check, ensure SECRET_KEY is set before we even check for database connectivity
if CONFIG.get("secret_key") is None or len(CONFIG.get("secret_key")) == 0:
    LOGGER.info("----------------------------------------------------------------------")
    LOGGER.info("Secret key missing, check https://goauthentik.io/docs/installation/.")
    LOGGER.info("----------------------------------------------------------------------")
    sysexit(1)


while True:
    try:
        conn = connect(
            dbname=CONFIG.get("postgresql.name"),
            user=CONFIG.get("postgresql.user"),
            password=CONFIG.get("postgresql.password"),
            host=CONFIG.get("postgresql.host"),
            port=CONFIG.get_int("postgresql.port"),
            sslmode=CONFIG.get("postgresql.sslmode"),
            sslrootcert=CONFIG.get("postgresql.sslrootcert"),
            sslcert=CONFIG.get("postgresql.sslcert"),
            sslkey=CONFIG.get("postgresql.sslkey"),
        )
        conn.cursor()
        break
    except OperationalError as exc:
        sleep(1)
        LOGGER.info(f"PostgreSQL connection failed, retrying... ({exc})")
LOGGER.info("PostgreSQL connection successful")

REDIS_PROTOCOL_PREFIX = "redis://"
if CONFIG.get_bool("redis.tls", False):
    REDIS_PROTOCOL_PREFIX = "rediss://"
REDIS_URL = (
    f"{REDIS_PROTOCOL_PREFIX}:"
    f"{quote_plus(CONFIG.get('redis.password'))}@{quote_plus(CONFIG.get('redis.host'))}:"
    f"{CONFIG.get_int('redis.port')}/{CONFIG.get('redis.db')}"
)
while True:
    try:
        redis = Redis.from_url(REDIS_URL)
        redis.ping()
        break
    except RedisError as exc:
        sleep(1)
        LOGGER.info(f"Redis Connection failed, retrying... ({exc})", redis_url=REDIS_URL)
LOGGER.info("Redis Connection successful")

LOGGER.info("Finished authentik bootstrap")
