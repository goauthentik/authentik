"""Generate config for development"""
from yaml import safe_dump

from authentik.lib.generators import generate_id

with open("local.env.yml", "w", encoding="utf-8") as _config:
    safe_dump(
        {
            "log_level": "debug",
            "secret_key": generate_id(),
            "postgresql": {
                "user": "postgres",
            },
            "outposts": {
                "container_image_base": "ghcr.io/goauthentik/dev-%(type)s:gh-%(build_hash)s",
            },
            "blueprints_dir": "./blueprints",
            "web": {
                "outpost_port_offset": 100,
            },
            "cert_discovery_dir": "./certs",
            "geoip": "tests/GeoLite2-City-Test.mmdb",
        },
        _config,
        default_flow_style=False,
    )
