from os import getenv
from typing import Any

from yaml import safe_dump

from authentik.lib.generators import generate_id

config: dict[str, Any] = {
    "log_level": "debug",
    "secret_key": generate_id(),
}

profiles = getenv("PROFILES")
if profiles and "postgres_replica" in profiles:
    config["postgresql"] = {"read_replicas": {"0": {"host": "localhost", "port": 5433}}}

with open("local.env.yml", "w") as _config:
    safe_dump(config, _config, default_flow_style=False)
