#!/usr/bin/env python3

"""Generate the Quadlet unit files under ``lifecycle/quadlet/``.

Mirrors ``scripts/generate_compose.py``: the authentik image tag is pinned to
``authentik_version()`` so ``make bump`` rewrites these unit files on every
release in lockstep with ``lifecycle/container/compose.yml``.

Quadlet does not expand ``${VAR}`` in ``Image=``, so the tag is written
literally rather than wrapped in a compose-style ``${AUTHENTIK_TAG:-...}``
fallback.

Two unit sets are emitted:

* ``lifecycle/quadlet/`` — rootful, dropped into ``/etc/containers/systemd/``.
* ``lifecycle/quadlet/rootless/`` — rootless, dropped into
  ``~/.config/containers/systemd/``. Uses systemd specifiers ``%h`` (home) and
  ``%t`` (``$XDG_RUNTIME_DIR``) so a single file works for any rootless user.
"""

from pathlib import Path

from packaging.version import parse

from authentik import authentik_version

version = authentik_version()
version_parsed = parse(version)
version_split = version_parsed.base_version.split(".")
# Mirror generate_compose.py: for an rc on a patch release (e.g. 2026.2.2-rc1)
# fall back to the previous released patch so the pinned tag is always pullable.
if version_parsed.is_prerelease and version_split[-1] != "0":
    previous_patch = int(version_split[-1]) - 1
    version_split[-1] = str(previous_patch)
    version = ".".join(version_split)

AUTHENTIK_IMAGE = f"ghcr.io/goauthentik/server:{version}"
POSTGRES_IMAGE = "docker.io/library/postgres:16-alpine"

OUTPUT_DIR = Path("lifecycle/quadlet")
ROOTLESS_DIR = OUTPUT_DIR / "rootless"

Entry = tuple[str, str]
Unit = dict[str, tuple[Entry, ...]]


def render_unit(sections: Unit) -> str:
    rendered_sections = []
    for name, entries in sections.items():
        lines = [f"[{name}]"]
        lines.extend(f"{key}={value}" for key, value in entries)
        rendered_sections.append("\n".join(lines))
    return "\n\n".join(rendered_sections) + "\n"


def pod() -> Unit:
    return {
        "Unit": (("Description", "authentik"),),
        "Pod": (
            ("PodName", "authentik"),
            ("PublishPort", "9000:9000"),
            ("PublishPort", "9443:9443"),
        ),
        "Install": (("WantedBy", "default.target"),),
    }


def database_volume() -> Unit:
    return {"Volume": (("VolumeName", "authentik-database"),)}


def postgresql_container(env_file: str) -> Unit:
    return {
        "Unit": (("Description", "authentik PostgreSQL"),),
        "Container": (
            ("ContainerName", "authentik-postgresql"),
            ("Image", POSTGRES_IMAGE),
            ("AutoUpdate", "registry"),
            ("Pod", "authentik.pod"),
            ("Volume", "authentik-database.volume:/var/lib/postgresql/data"),
            ("EnvironmentFile", env_file),
            ("Environment", "POSTGRES_DB=authentik"),
            ("Environment", "POSTGRES_USER=authentik"),
            ("HealthCmd", "pg_isready -d authentik -U authentik"),
            ("HealthInterval", "30s"),
            ("HealthStartPeriod", "20s"),
            ("HealthTimeout", "5s"),
            ("HealthRetries", "5"),
        ),
        "Service": (("Restart", "always"),),
        "Install": (("WantedBy", "default.target"),),
    }


def server_container(env_file: str, data_dir: str) -> Unit:
    return {
        "Unit": (
            ("Description", "authentik server"),
            ("Requires", "authentik-postgresql.container"),
            ("After", "authentik-postgresql.container"),
        ),
        "Container": (
            ("ContainerName", "authentik-server"),
            ("Image", AUTHENTIK_IMAGE),
            ("AutoUpdate", "registry"),
            ("Pod", "authentik.pod"),
            ("Exec", "server"),
            ("EnvironmentFile", env_file),
            ("Environment", "AUTHENTIK_POSTGRESQL__HOST=localhost"),
            ("Environment", "AUTHENTIK_POSTGRESQL__NAME=authentik"),
            ("Environment", "AUTHENTIK_POSTGRESQL__USER=authentik"),
            ("Volume", f"{data_dir}/data:/data:Z"),
            ("Volume", f"{data_dir}/custom-templates:/templates:Z"),
            ("ShmSize", "512m"),
        ),
        "Service": (("Restart", "always"),),
        "Install": (("WantedBy", "default.target"),),
    }


def worker_container(env_file: str, data_dir: str, podman_sock_dir: str) -> Unit:
    return {
        "Unit": (
            ("Description", "authentik worker"),
            ("Requires", "authentik-postgresql.container"),
            ("After", "authentik-postgresql.container"),
        ),
        "Container": (
            ("ContainerName", "authentik-worker"),
            ("Image", AUTHENTIK_IMAGE),
            ("AutoUpdate", "registry"),
            ("Pod", "authentik.pod"),
            ("Exec", "worker"),
            ("User", "0:0"),
            ("EnvironmentFile", env_file),
            ("Environment", "AUTHENTIK_POSTGRESQL__HOST=localhost"),
            ("Environment", "AUTHENTIK_POSTGRESQL__NAME=authentik"),
            ("Environment", "AUTHENTIK_POSTGRESQL__USER=authentik"),
            ("Environment", "AUTHENTIK_LISTEN__HTTP=0.0.0.0:9001"),
            ("Environment", "AUTHENTIK_LISTEN__METRICS=0.0.0.0:9301"),
            (
                "Volume",
                f"{podman_sock_dir}/podman/podman.sock:/run/podman/podman.sock:Z",
            ),
            ("Volume", f"{data_dir}/data:/data:Z"),
            ("Volume", f"{data_dir}/certs:/certs:Z"),
            ("Volume", f"{data_dir}/custom-templates:/templates:Z"),
            ("ShmSize", "512m"),
        ),
        "Service": (("Restart", "always"),),
        "Install": (("WantedBy", "default.target"),),
    }


ROOTFUL = {
    "authentik.pod": pod(),
    "authentik-database.volume": database_volume(),
    "authentik-postgresql.container": postgresql_container(
        env_file="/etc/authentik/authentik.env",
    ),
    "authentik-server.container": server_container(
        env_file="/etc/authentik/authentik.env",
        data_dir="/var/lib/authentik",
    ),
    "authentik-worker.container": worker_container(
        env_file="/etc/authentik/authentik.env",
        data_dir="/var/lib/authentik",
        podman_sock_dir="/run",
    ),
}

ROOTLESS = {
    "authentik.pod": pod(),
    "authentik-database.volume": database_volume(),
    "authentik-postgresql.container": postgresql_container(
        env_file="%h/.config/authentik/authentik.env",
    ),
    "authentik-server.container": server_container(
        env_file="%h/.config/authentik/authentik.env",
        data_dir="%h/.local/share/authentik",
    ),
    "authentik-worker.container": worker_container(
        env_file="%h/.config/authentik/authentik.env",
        data_dir="%h/.local/share/authentik",
        podman_sock_dir="%t",
    ),
}


def write(target: Path, units: dict[str, Unit]) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for name, unit in units.items():
        (target / name).write_text(render_unit(unit))


write(OUTPUT_DIR, ROOTFUL)
write(ROOTLESS_DIR, ROOTLESS)
