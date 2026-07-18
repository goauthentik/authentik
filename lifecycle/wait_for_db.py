#!/usr/bin/env python
"""This file needs to be run from the root of the project to correctly
import authentik. This is done by the dockerfile."""

from sys import exit as sysexit
from time import sleep

from psycopg import OperationalError, connect

from authentik.lib.config import CONFIG

CHECK_THRESHOLD = 30


def check_postgres():
    attempt = 0
    while True:
        if attempt >= CHECK_THRESHOLD:
            sysexit(1)
        try:
            conn_opts = CONFIG.get_dict_from_b64_json("postgresql.conn_options", default={})
            conn = connect(
                dbname=CONFIG.refresh("postgresql.name"),
                user=CONFIG.refresh("postgresql.user"),
                password=CONFIG.refresh("postgresql.password"),
                host=CONFIG.refresh("postgresql.host"),
                port=CONFIG.get_int("postgresql.port"),
                sslmode=CONFIG.get("postgresql.sslmode"),
                sslrootcert=CONFIG.get("postgresql.sslrootcert"),
                sslcert=CONFIG.get("postgresql.sslcert"),
                sslkey=CONFIG.get("postgresql.sslkey"),
                **conn_opts,
            )
            conn.cursor()
            break
        except OperationalError as exc:
            sleep(1)
            CONFIG.log("info", f"PostgreSQL connection failed, retrying... ({exc})")
        finally:
            attempt += 1
    CONFIG.log("info", "PostgreSQL connection successful")


def wait_for_db():
    CONFIG.log("info", "Starting authentik bootstrap")
    # Sanity check, ensure SECRET_KEY is set before we even check for database connectivity
    if CONFIG.get("secret_key") is None or len(CONFIG.get("secret_key")) == 0:
        CONFIG.log("info", "----------------------------------------------------------------------")
        CONFIG.log(
            "info", "Secret key missing, check https://docs.goauthentik.io/docs/install-config/"
        )
        CONFIG.log("info", "----------------------------------------------------------------------")
        sysexit(1)
    check_postgres()
    CONFIG.log("info", "Finished authentik bootstrap")


if __name__ == "__main__":
    wait_for_db()
