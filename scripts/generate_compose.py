#!/usr/bin/env python3

from packaging.version import parse
from yaml import safe_dump

from authentik import authentik_version

version = authentik_version()
version_parsed = parse(version)
version_split = version_parsed.base_version.split(".")
# If this is an rc version for a patch release (i.e. 2026.2.2-rc1), then don't include that in the
# compose, and fallback to the previous released patch version
if version_parsed.is_prerelease and version_split[-1] != "0":
    previous_patch = int(version_split[-1]) - 1
    version_split[-1] = str(previous_patch)
    version = ".".join(version_split)

authentik_image = f"${{AUTHENTIK_IMAGE:-ghcr.io/goauthentik/server}}:${{AUTHENTIK_TAG:-{version}}}"

base = {
    "services": {
        "postgresql": {
            "env_file": [".env"],
            "environment": {
                "POSTGRES_DB": "${PG_DB:-authentik}",
                "POSTGRES_PASSWORD": "${PG_PASS:?database password required}",
                "POSTGRES_USER": "${PG_USER:-authentik}",
            },
            "healthcheck": {
                "interval": "30s",
                "retries": 5,
                "start_period": "20s",
                "test": ["CMD-SHELL", "pg_isready -d $${POSTGRES_DB} -U $${POSTGRES_USER}"],
                "timeout": "5s",
            },
            "image": "docker.io/library/postgres:16-alpine",
            "restart": "unless-stopped",
            "volumes": ["database:/var/lib/postgresql/data"],
        },
        "server": {
            "command": "server",
            "depends_on": {
                "postgresql": {"condition": "service_healthy"},
            },
            "env_file": [".env"],
            "environment": {
                "AUTHENTIK_POSTGRESQL__HOST": "postgresql",
                "AUTHENTIK_POSTGRESQL__NAME": "${PG_DB:-authentik}",
                "AUTHENTIK_POSTGRESQL__PASSWORD": "${PG_PASS}",
                "AUTHENTIK_POSTGRESQL__USER": "${PG_USER:-authentik}",
                "AUTHENTIK_SECRET_KEY": "${AUTHENTIK_SECRET_KEY:?secret key required}",
            },
            "shm_size": "512mb",
            "image": authentik_image,
            "ports": ["${COMPOSE_PORT_HTTP:-9000}:9000", "${COMPOSE_PORT_HTTPS:-9443}:9443"],
            "restart": "unless-stopped",
            "volumes": ["./data:/data", "./custom-templates:/templates"],
        },
        "worker": {
            "command": "worker",
            "depends_on": {
                "postgresql": {"condition": "service_healthy"},
            },
            "env_file": [".env"],
            "environment": {
                "AUTHENTIK_POSTGRESQL__HOST": "postgresql",
                "AUTHENTIK_POSTGRESQL__NAME": "${PG_DB:-authentik}",
                "AUTHENTIK_POSTGRESQL__PASSWORD": "${PG_PASS}",
                "AUTHENTIK_POSTGRESQL__USER": "${PG_USER:-authentik}",
                "AUTHENTIK_SECRET_KEY": "${AUTHENTIK_SECRET_KEY:?secret key required}",
            },
            "shm_size": "512mb",
            "image": authentik_image,
            "restart": "unless-stopped",
            "user": "root",
            "volumes": [
                "/var/run/docker.sock:/var/run/docker.sock",
                "./data:/data",
                "./certs:/certs",
                "./custom-templates:/templates",
            ],
        },
    },
    "volumes": {
        "database": {
            "driver": "local",
        },
    },
}

with open("lifecycle/container/compose.yml", "w") as _compose:
    safe_dump(base, _compose)
