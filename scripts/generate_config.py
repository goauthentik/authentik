#!/usr/bin/env python3
"""Generate config for development"""

from yaml import safe_dump

from authentik.lib.generators import generate_id


def generate_local_config():
    """Generate a local development configuration"""
    # TODO: This should be generated and validated against a schema, such as Pydantic.

    return {
        "debug": True,
        "log_level": "debug",
        "secret_key": generate_id(),
        "postgresql": {
            "user": "postgres",
        },
        "outposts": {
            "container_image_base": "ghcr.io/goauthentik/dev-%(type)s:gh-%(build_hash)s",
            "disable_embedded_outpost": False,
        },
        "blueprints_dir": "./blueprints",
        "cert_discovery_dir": "./certs",
        "events": {
            "processors": {
                "geoip": "tests/GeoLite2-City-Test.mmdb",
                "asn": "tests/GeoLite2-ASN-Test.mmdb",
            }
        },
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
        "tenants": {
            "enabled": False,
            "api_key": generate_id(),
        },
        "worker": {
            "processes": 1,
            "threads": 1,
            "consumer_listen_timeout": "seconds=10",
            "scheduler_interval": "seconds=30",
        },
    }


if __name__ == "__main__":
    config_file_name = "local.env.yml"

    with open(config_file_name, "w", encoding="utf-8") as _config:
        _config.write(
            """
# Local authentik configuration overrides
#
# https://docs.goauthentik.io/docs/install-config/configuration/
#
# To regenerate this file, run the following command from the repository root:
#
# ```shell
# make gen-dev-config
# ```

"""
        )

        safe_dump(
            generate_local_config(),
            _config,
            default_flow_style=False,
        )

    print(
        f"""
---

Generated configuration file: {config_file_name}

For more information on how to use this configuration, see:

https://docs.goauthentik.io/docs/install-config/configuration/

---
"""
    )
