"""authentik core config loader"""

import base64
import json
import os
from collections.abc import Mapping
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from glob import glob
from json import JSONEncoder, dumps, loads
from json.decoder import JSONDecodeError
from pathlib import Path
from sys import argv, stderr
from time import time
from typing import Any
from urllib.parse import urlparse

import yaml
from django.conf import ImproperlyConfigured

from authentik.lib.utils.dict import delete_path_in_dict, get_path_from_dict, set_path_in_dict

SEARCH_PATHS = ["authentik/lib/default.yml", "/etc/authentik/config.yml", ""] + glob(
    "/etc/authentik/config.d/*.yml", recursive=True
)
ENV_PREFIX = "AUTHENTIK"
ENVIRONMENT = os.getenv(f"{ENV_PREFIX}_ENV", "local")

# Old key -> new key
DEPRECATIONS = {
    "geoip": "events.context_processors.geoip",
    "worker.concurrency": "worker.threads",
}


@dataclass(slots=True)
class Attr:
    """Single configuration attribute"""

    class Source(Enum):
        """Sources a configuration attribute can come from, determines what should be done with
        Attr.source (and if it's set at all)"""

        UNSPECIFIED = "unspecified"
        ENV = "env"
        CONFIG_FILE = "config_file"
        URI = "uri"

    value: Any

    source_type: Source = field(default=Source.UNSPECIFIED)

    # depending on source_type, might contain the environment variable or the path
    # to the config file containing this change or the file containing this value
    source: str | None = field(default=None)

    def __post_init__(self):
        if isinstance(self.value, Attr):
            raise RuntimeError(f"config Attr with nested Attr for source {self.source}")


class AttrEncoder(JSONEncoder):
    """JSON encoder that can deal with `Attr` classes"""

    def default(self, o: Any) -> Any:
        if isinstance(o, Attr):
            return o.value
        return super().default(o)


class UNSET:
    """Used to test whether configuration key has not been set."""


class ConfigLoader:
    """Search through SEARCH_PATHS and load configuration. Environment variables starting with
    `ENV_PREFIX` are also applied.

    A variable like AUTHENTIK_POSTGRESQL__HOST would translate to postgresql.host"""

    deprecations: dict[tuple[str, str], str] = {}

    def __init__(self, **kwargs):
        super().__init__()
        self.__config = {}
        base_dir = Path(__file__).parent.joinpath(Path("../..")).resolve()
        for _path in SEARCH_PATHS:
            path = Path(_path)
            # Check if path is relative, and if so join with base_dir
            if not path.is_absolute():
                path = base_dir / path
            if path.is_file() and path.exists():
                # Path is an existing file, so we just read it and update our config with it
                self.update_from_file(path)
            elif path.is_dir() and path.exists():
                # Path is an existing dir, so we try to read the env config from it
                env_paths = [
                    path / Path(ENVIRONMENT + ".yml"),
                    path / Path(ENVIRONMENT + ".env.yml"),
                    path / Path(ENVIRONMENT + ".yaml"),
                    path / Path(ENVIRONMENT + ".env.yaml"),
                ]
                for env_file in env_paths:
                    if env_file.is_file() and env_file.exists():
                        # Update config with env file
                        self.update_from_file(env_file)
        self.update_from_env()
        self.update(self.__config, kwargs)
        self.deprecations = self.check_deprecations()

    def check_deprecations(self) -> dict[str, str]:
        """Warn if any deprecated configuration options are used"""

        def _pop_deprecated_key(current_obj, dot_parts, index):
            """Recursive function to remove deprecated keys in configuration"""
            dot_part = dot_parts[index]
            if index == len(dot_parts) - 1:
                return current_obj.pop(dot_part)
            value = _pop_deprecated_key(current_obj[dot_part], dot_parts, index + 1)
            if not current_obj[dot_part]:
                current_obj.pop(dot_part)
            return value

        deprecation_replacements = {}
        for deprecation, replacement in DEPRECATIONS.items():
            if self.get(deprecation, default=UNSET) is UNSET:
                continue
            message = (
                f"'{deprecation}' has been deprecated in favor of '{replacement}'! "
                + "Please update your configuration."
            )
            self.log(
                "warning",
                message,
            )
            deprecation_replacements[(deprecation, replacement)] = message

            deprecated_attr = _pop_deprecated_key(self.__config, deprecation.split("."), 0)
            self.set(replacement, deprecated_attr)
        return deprecation_replacements

    def log(self, level: str, message: str, **kwargs):
        """Custom Log method, we want to ensure ConfigLoader always logs JSON even when
        'structlog' or 'logging' hasn't been configured yet."""
        output = {
            "event": message,
            "level": level,
            "logger": self.__class__.__module__,
            "timestamp": time(),
        }
        output.update(kwargs)
        print(dumps(output), file=stderr)

    def update(self, root: dict[str, Any], updatee: dict[str, Any]) -> dict[str, Any]:
        """Recursively update dictionary"""
        for key, raw_value in updatee.items():
            if isinstance(raw_value, Mapping):
                root[key] = self.update(root.get(key, {}), raw_value)
            else:
                if isinstance(raw_value, str):
                    value = self.parse_uri(raw_value)
                elif isinstance(raw_value, Attr) and isinstance(raw_value.value, str):
                    value = self.parse_uri(raw_value.value)
                elif not isinstance(raw_value, Attr):
                    value = Attr(raw_value)
                else:
                    value = raw_value
                root[key] = value
        return root

    def refresh(self, key: str, default=None, sep=".") -> Any:
        """Update a single value"""
        attr: Attr = get_path_from_dict(self.raw, key, sep=sep, default=Attr(default))
        if attr.source_type != Attr.Source.URI:
            return attr.value
        attr.value = self.parse_uri(attr.source).value
        return attr.value

    def parse_uri(self, value: str) -> Attr:
        """Parse string values which start with a URI"""
        url = urlparse(value)
        parsed_value = value
        if url.scheme == "env":
            parsed_value = os.getenv(url.netloc, url.query)
        if url.scheme == "file":
            try:
                with open(url.path, encoding="utf8") as _file:
                    parsed_value = _file.read().strip()
            except OSError as exc:
                self.log("error", f"Failed to read config value from {url.path}: {exc}")
                parsed_value = url.query
        return Attr(parsed_value, Attr.Source.URI, value)

    def update_from_file(self, path: Path):
        """Update config from file contents"""
        try:
            with open(path, encoding="utf8") as file:
                try:
                    self.update(self.__config, yaml.safe_load(file))
                    self.log("debug", "Loaded config", file=str(path))
                except yaml.YAMLError as exc:
                    raise ImproperlyConfigured from exc
        except PermissionError as exc:
            self.log(
                "warning",
                "Permission denied while reading file",
                path=path,
                error=str(exc),
            )

    def update_from_dict(self, update: dict):
        """Update config from dict"""
        self.__config.update(update)

    def update_from_env(self):
        """Check environment variables"""
        outer = {}
        idx = 0
        for key, value in os.environ.items():
            if not key.startswith(ENV_PREFIX):
                continue
            relative_key = key.replace(f"{ENV_PREFIX}_", "", 1).replace("__", ".").lower()
            # Check if the value is json, and try to load it
            try:
                value = loads(value)  # noqa: PLW2901
            except JSONDecodeError:
                pass
            attr_value = Attr(value, Attr.Source.ENV, relative_key)
            set_path_in_dict(outer, relative_key, attr_value)
            idx += 1
        if idx > 0:
            self.log("debug", "Loaded environment variables", count=idx)
            self.update(self.__config, outer)

    @contextmanager
    def patch(self, path: str, value: Any):
        """Context manager for unittests to patch a value"""
        original_value = self.get(path, UNSET)
        self.set(path, value)
        try:
            yield
        finally:
            if original_value is not UNSET:
                self.set(path, original_value)
            else:
                self.delete(path)

    @property
    def raw(self) -> dict:
        """Get raw config dictionary"""
        return self.__config

    def get(self, path: str, default=None, sep=".") -> Any:
        """Access attribute by using yaml path"""
        # Walk sub_dicts before parsing path
        root = self.raw
        # Walk each component of the path
        attr: Attr = get_path_from_dict(root, path, sep=sep, default=Attr(default))
        return attr.value

    def get_int(self, path: str, default=0) -> int:
        """Wrapper for get that converts value into int"""
        try:
            return int(self.get(path, default))
        except ValueError as exc:
            self.log("warning", "Failed to parse config as int", path=path, exc=str(exc))
            return default

    def get_optional_int(self, path: str, default=None) -> int | None:
        """Wrapper for get that converts value into int or None if set"""
        value = self.get(path, UNSET)
        if value is UNSET:
            return default
        try:
            return int(value)
        except (ValueError, TypeError) as exc:
            if value is None or (isinstance(value, str) and value.lower() in ("", "null", "none")):
                return None
            self.log("warning", "Failed to parse config as int", path=path, exc=str(exc))
            return default

    def get_bool(self, path: str, default=False) -> bool:
        """Wrapper for get that converts value into boolean"""
        value = self.get(path, UNSET)
        if value is UNSET:
            return default
        return str(self.get(path)).lower() == "true"

    def get_keys(self, path: str, sep=".") -> list[str]:
        """List attribute keys by using yaml path"""
        root = self.raw
        attr: Attr = get_path_from_dict(root, path, sep=sep, default=Attr({}))
        return attr.keys()

    def get_dict_from_b64_json(self, path: str, default=None) -> dict:
        """Wrapper for get that converts value from Base64 encoded string into dictionary"""
        config_value = self.get(path)
        if config_value is None:
            return {}
        try:
            b64decoded_str = base64.b64decode(config_value).decode("utf-8")
            return json.loads(b64decoded_str)
        except (JSONDecodeError, TypeError, ValueError) as exc:
            self.log(
                "warning",
                f"Ignored invalid configuration for '{path}' due to exception: {str(exc)}",
            )
            return default if isinstance(default, dict) else {}

    def set(self, path: str, value: Any, sep="."):
        """Set value using same syntax as get()"""
        if not isinstance(value, Attr):
            value = Attr(value)
        set_path_in_dict(self.raw, path, value, sep=sep)

    def delete(self, path: str, sep="."):
        delete_path_in_dict(self.raw, path, sep=sep)


CONFIG = ConfigLoader()


# Reserved alias for the direct (un-pooled or session-mode-pooled) database
# connection. Used by code that needs a stable PG backend across calls:
# LISTEN/NOTIFY and session-scoped advisory locks. See ``django_db_config``.
DIRECT_DB_ALIAS = "direct"


def postgresql_direct_db_enabled(config: ConfigLoader | None = None) -> bool:
    """Whether a dedicated direct PostgreSQL endpoint has been configured.

    Returns True if any ``postgresql.direct.*`` key is set. When True, a Django
    connection at alias ``direct`` is added; subsystems that hold server-side
    state (LISTEN/NOTIFY, advisory locks) route through it so an operator can
    put a transaction-pooling pooler in front of ``postgresql.host`` without
    breaking them.
    """
    if not config:
        config = CONFIG
    return any(
        config.get(f"postgresql.direct.{key}", default=UNSET) is not UNSET
        for key in (
            "host",
            "port",
            "name",
            "user",
            "password",
            "sslmode",
            "sslrootcert",
            "sslcert",
            "sslkey",
            "conn_options",
        )
    )


def postgresql_direct_connection_kwargs(config: ConfigLoader | None = None) -> dict:
    """Return kwargs suitable for ``psycopg.connect()`` for the direct endpoint.

    Reads ``postgresql.direct.*`` overrides, falling back to ``postgresql.*``
    for unset keys. Used by ``lifecycle/migrate.py`` for the startup advisory
    lock.
    """
    if not config:
        config = CONFIG

    def _override(field: str, default):
        return config.get(f"postgresql.direct.{field}", default=default)

    kwargs = {
        "host": _override("host", config.get("postgresql.host")),
        "port": _override("port", config.get_int("postgresql.port", 5432)),
        "dbname": _override("name", config.get("postgresql.name")),
        "user": _override("user", config.get("postgresql.user")),
        "password": _override("password", config.get("postgresql.password")),
        "sslmode": _override("sslmode", config.get("postgresql.sslmode")),
        "sslrootcert": _override("sslrootcert", config.get("postgresql.sslrootcert")),
        "sslcert": _override("sslcert", config.get("postgresql.sslcert")),
        "sslkey": _override("sslkey", config.get("postgresql.sslkey")),
    }
    # direct.conn_options wins over the main conn_options when both are set.
    conn_opts = config.get_dict_from_b64_json("postgresql.conn_options", default={})
    direct_conn_opts = config.get_dict_from_b64_json("postgresql.direct.conn_options", default={})
    kwargs.update(conn_opts)
    kwargs.update(direct_conn_opts)
    return {k: v for k, v in kwargs.items() if v is not None}


def _build_direct_db_alias(default_db: dict, config: ConfigLoader) -> dict:
    """Build the ``direct`` Django DB alias dict from a copy of the default
    alias plus ``postgresql.direct.*`` overrides."""
    direct_db = deepcopy(default_db)
    direct_kwargs = postgresql_direct_connection_kwargs(config)
    direct_db["HOST"] = direct_kwargs.get("host")
    direct_db["PORT"] = direct_kwargs.get("port")
    direct_db["NAME"] = direct_kwargs.get("dbname")
    direct_db["USER"] = direct_kwargs.get("user")
    direct_db["PASSWORD"] = direct_kwargs.get("password")
    direct_db["OPTIONS"] = {
        "sslmode": direct_kwargs.get("sslmode"),
        "sslrootcert": direct_kwargs.get("sslrootcert"),
        "sslcert": direct_kwargs.get("sslcert"),
        "sslkey": direct_kwargs.get("sslkey"),
        "pool": False,
    }
    # Carry over extra option keys (e.g. application_name) from direct.conn_options.
    for key, value in direct_kwargs.items():
        if key in ("host", "port", "dbname", "user", "password"):
            continue
        if key in direct_db["OPTIONS"]:
            continue
        direct_db["OPTIONS"][key] = value
    # Persistent connections: managed by the broker / channel layer, not
    # subject to per-request close_old_connections().
    direct_db["CONN_MAX_AGE"] = None
    direct_db["CONN_HEALTH_CHECKS"] = False
    direct_db["DISABLE_SERVER_SIDE_CURSORS"] = True
    direct_db["OPTIONS"] = {k: v for k, v in direct_db["OPTIONS"].items() if v is not None}
    return direct_db


def django_db_config(config: ConfigLoader | None = None) -> dict:
    if not config:
        config = CONFIG

    pool_options = False
    use_pool = config.get_bool("postgresql.use_pool", False)
    if use_pool:
        pool_options = config.get_dict_from_b64_json("postgresql.pool_options", True)
        if not pool_options:
            pool_options = True
    # FIXME: Temporarily force pool to be deactivated.
    # See https://github.com/goauthentik/authentik/issues/14320
    pool_options = False

    conn_options = config.get_dict_from_b64_json("postgresql.conn_options", default={})

    db = {
        "default": {
            "ENGINE": "psqlextra.backend",
            "HOST": config.get("postgresql.host"),
            "NAME": config.get("postgresql.name"),
            "USER": config.get("postgresql.user"),
            "PASSWORD": config.get("postgresql.password"),
            "PORT": config.get("postgresql.port"),
            "OPTIONS": {
                "sslmode": config.get("postgresql.sslmode"),
                "sslrootcert": config.get("postgresql.sslrootcert"),
                "sslcert": config.get("postgresql.sslcert"),
                "sslkey": config.get("postgresql.sslkey"),
                "pool": pool_options,
                **conn_options,
            },
            "CONN_MAX_AGE": config.get_optional_int("postgresql.conn_max_age", 0),
            "CONN_HEALTH_CHECKS": config.get_bool("postgresql.conn_health_checks", False),
            "DISABLE_SERVER_SIDE_CURSORS": config.get_bool(
                "postgresql.disable_server_side_cursors", False
            ),
            "TEST": {
                "NAME": config.get("postgresql.test.name"),
            },
        }
    }

    conn_max_age = config.get_optional_int("postgresql.conn_max_age", UNSET)
    disable_server_side_cursors = config.get_bool("postgresql.disable_server_side_cursors", UNSET)
    if config.get_bool("postgresql.use_pgpool", False):
        db["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
        if disable_server_side_cursors is not UNSET:
            db["default"]["DISABLE_SERVER_SIDE_CURSORS"] = disable_server_side_cursors

    if config.get_bool("postgresql.use_pgbouncer", False):
        # https://docs.djangoproject.com/en/4.0/ref/databases/#transaction-pooling-server-side-cursors
        db["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
        # https://docs.djangoproject.com/en/4.0/ref/databases/#persistent-connections
        db["default"]["CONN_MAX_AGE"] = None  # persistent
        if disable_server_side_cursors is not UNSET:
            db["default"]["DISABLE_SERVER_SIDE_CURSORS"] = disable_server_side_cursors
        if conn_max_age is not UNSET:
            db["default"]["CONN_MAX_AGE"] = conn_max_age

    all_replica_conn_options = config.get_dict_from_b64_json(
        "postgresql.replica_conn_options",
        default={},
    )

    for replica in config.get_keys("postgresql.read_replicas"):
        _database = deepcopy(db["default"])

        for setting, current_value in db["default"].items():
            if isinstance(current_value, dict):
                continue
            override = config.get(
                f"postgresql.read_replicas.{replica}.{setting.lower()}", default=UNSET
            )
            if override is not UNSET:
                _database[setting] = override

        for option in conn_options.keys():
            _database["OPTIONS"].pop(option, None)

        for setting in db["default"]["OPTIONS"].keys():
            override = config.get(
                f"postgresql.read_replicas.{replica}.{setting.lower()}", default=UNSET
            )
            if override is not UNSET:
                _database["OPTIONS"][setting] = override

        _database["OPTIONS"].update(all_replica_conn_options)
        replica_conn_options = config.get_dict_from_b64_json(
            f"postgresql.read_replicas.{replica}.conn_options", default={}
        )
        _database["OPTIONS"].update(replica_conn_options)

        db[f"replica_{replica}"] = _database

    # Optional direct endpoint for LISTEN/NOTIFY and advisory-lock connections.
    # Only added when operator sets ``postgresql.direct.*``; excluded from
    # replica routing and migrations by ``authentik.tenants.db.FailoverRouter``.
    if postgresql_direct_db_enabled(config):
        db[DIRECT_DB_ALIAS] = _build_direct_db_alias(db["default"], config)

    return db


if __name__ == "__main__":
    if len(argv) < 2:  # noqa: PLR2004
        print(dumps(CONFIG.raw, indent=4, cls=AttrEncoder))
    else:
        for arg in argv[1:]:
            print(CONFIG.get(arg))
