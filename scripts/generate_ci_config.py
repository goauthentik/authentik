"""Utility script to generate a config for CI runs"""
from authentik.providers.oauth2.generators import generate_client_id
from yaml import safe_dump

with open("local.env.yml", "w") as _config:
    safe_dump({
        "secret_key": generate_client_id()
    }, _config, default_flow_style=False)
