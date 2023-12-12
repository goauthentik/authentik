"""Generate config for development"""
from yaml import safe_dump

from authentik.lib.generators import generate_id

with open("local.env.yml", "w", encoding="utf-8") as _config:
    safe_dump(
        {
            "debug": True,
            "log_level": "debug",
            "secret_key": generate_id(),
            "postgresql": {
                "user": "postgres",
            },
            "outposts": {
                "container_image_base": "ghcr.io/goauthentik/dev-%(type)s:gh-%(build_hash)s",
            },
            "blueprints_dir": "./blueprints",
            "cert_discovery_dir": "./certs",
            "geoip": "tests/GeoLite2-City-Test.mmdb",
            "storage": {
                "media": {
                    "backend": "file",
                    "s3": {
                        "endpoint": "http://localhost:8020",
                        "access_key": "accessKey1",
                        "secret_key": "secretKey1",
                        "bucket_name": "authentik-media",
                        "custom_domain": "localhost:8020/authentik-media",
                        "secure_urls": False,
                    },
                },
            },
        },
        _config,
        default_flow_style=False,
    )
