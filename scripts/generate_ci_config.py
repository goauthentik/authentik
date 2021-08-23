"""Utility script to generate a config for CI runs"""
from authentik.lib.generators import generate_id
from yaml import safe_dump

with open("local.env.yml", "w") as _config:
    safe_dump({
        "log_level": "debug",
        "secret_key": generate_id(),
    }, _config, default_flow_style=False)
