#!/usr/bin/env python
"""This file needs to be run from the root of the project to correctly
import authentik. This is done by the dockerfile."""
from sys import exit as sysexit
from time import sleep

from psycopg import OperationalError, connect
from redis.exceptions import RedisError

from authentik.lib.config import CONFIG
from authentik.lib.utils.parser import parse_url


def check_postgres():
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
            CONFIG.log("info", f"PostgreSQL connection failed, retrying... ({exc})")
    CONFIG.log("info", "PostgreSQL connection successful")


def check_redis():
    url = CONFIG.get("redis.url")
    while True:
        try:
            redis = parse_url(url)
            redis.ping()
            break
        # Catch index error for Redis cluster that is still initializing
        except (RedisError, IndexError) as exc:
            sleep(1)
            CONFIG.log("info", f"Redis Connection failed, retrying... ({exc})")
    CONFIG.log("info", "Redis Connection successful")


def wait_for_db():
    CONFIG.log("info", "Starting authentik bootstrap")
    # Sanity check, ensure SECRET_KEY is set before we even check for database connectivity
    if CONFIG.get("secret_key") is None or len(CONFIG.get("secret_key")) == 0:
        CONFIG.log("info", "----------------------------------------------------------------------")
        CONFIG.log("info", "Secret key missing, check https://goauthentik.io/docs/installation/.")
        CONFIG.log("info", "----------------------------------------------------------------------")
        sysexit(1)
    check_postgres()
    check_redis()
    CONFIG.log("info", "Finished authentik bootstrap")


if __name__ == "__main__":
    wait_for_db()
