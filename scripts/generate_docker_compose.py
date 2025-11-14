from yaml import safe_dump

from authentik import authentik_version

authentik_image = (
    f"${{AUTHENTIK_IMAGE:-ghcr.io/goauthentik/server}}:${{AUTHENTIK_TAG:-{authentik_version()}}}"
)

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
            "image": authentik_image,
            "ports": ["${COMPOSE_PORT_HTTP:-9000}:9000", "${COMPOSE_PORT_HTTPS:-9443}:9443"],
            "restart": "unless-stopped",
            "volumes": ["./media:/data/media", "./custom-templates:/templates"],
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
            "image": authentik_image,
            "restart": "unless-stopped",
            "user": "root",
            "volumes": [
                "/var/run/docker.sock:/var/run/docker.sock",
                "./media:/data/media",
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

with open("docker-compose.yml", "w") as _compose:
    safe_dump(base, _compose)
