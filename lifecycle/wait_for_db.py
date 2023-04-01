#!/usr/bin/env python
"""This file needs to be run from the root of the project to correctly
import authentik. This is done by the dockerfile."""
from sys import exit as sysexit
from time import sleep
from urllib.parse import quote_plus

from psycopg2 import OperationalError, connect
from redis.exceptions import RedisError

from authentik.lib.config import CONFIG

import redis_sentinel_url

CONFIG.log("info", "Starting authentik bootstrap")

# Sanity check, ensure SECRET_KEY is set before we even check for database connectivity
if CONFIG.y("secret_key") is None or len(CONFIG.y("secret_key")) == 0:
    CONFIG.log("info", "----------------------------------------------------------------------")
    CONFIG.log("info", "Secret key missing, check https://goauthentik.io/docs/installation/.")
    CONFIG.log("info", "----------------------------------------------------------------------")
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
        CONFIG.log("info", f"PostgreSQL connection failed, retrying... ({exc})")
CONFIG.log("info", "PostgreSQL connection successful")

REDIS_URL = CONFIG.y('redis.url')
while True:
    try:
        _, redis = redis_sentinel_url.connect(REDIS_URL)
        redis.ping()
        break
    except RedisError as exc:
        sleep(1)
        CONFIG.log("info", f"Redis Connection failed, retrying... ({exc})", redis_url=REDIS_URL)
CONFIG.log("info", "Redis Connection successful")

CONFIG.log("info", "Finished authentik bootstrap")
