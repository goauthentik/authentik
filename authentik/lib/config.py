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
from urllib.parse import quote_plus, urlparse

import yaml
from django.conf import ImproperlyConfigured

from authentik.lib.utils.dict import get_path_from_dict, set_path_in_dict

SEARCH_PATHS = ["authentik/lib/default.yml", "/etc/authentik/config.yml", ""] + glob(
    "/etc/authentik/config.d/*.yml", recursive=True
)
ENV_PREFIX = "AUTHENTIK"
ENVIRONMENT = os.getenv(f"{ENV_PREFIX}_ENV", "local")

REDIS_ENV_KEYS = [
    f"{ENV_PREFIX}_REDIS__HOST",
    f"{ENV_PREFIX}_REDIS__PORT",
    f"{ENV_PREFIX}_REDIS__DB",
    f"{ENV_PREFIX}_REDIS__USERNAME",
    f"{ENV_PREFIX}_REDIS__PASSWORD",
    f"{ENV_PREFIX}_REDIS__TLS",
    f"{ENV_PREFIX}_REDIS__TLS_REQS",
]

# Old key -> new key
DEPRECATIONS = {
    "geoip": "events.context_processors.geoip",
    "redis.broker_url": "broker.url",
    "redis.broker_transport_options": "broker.transport_options",
    "redis.cache_timeout": "cache.timeout",
    "redis.cache_timeout_flows": "cache.timeout_flows",
    "redis.cache_timeout_policies": "cache.timeout_policies",
    "redis.cache_timeout_reputation": "cache.timeout_reputation",
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
        original_value = self.get(path)
        self.set(path, value)
        try:
            yield
        finally:
            self.set(path, original_value)

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
        value = self.get(path, default)
        if value is UNSET:
            return default
        try:
            return int(value)
        except (ValueError, TypeError) as exc:
            if value is None or (isinstance(value, str) and value.lower() == "null"):
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
            b64decoded_str = b64decoded_str.strip().lstrip("{").rstrip("}")
            b64decoded_str = "{" + b64decoded_str + "}"
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


CONFIG = ConfigLoader()


def redis_url(db: int) -> str:
    """Helper to create a Redis URL for a specific database"""
    _redis_protocol_prefix = "redis://"
    _redis_tls_requirements = ""
    if CONFIG.get_bool("redis.tls", False):
        _redis_protocol_prefix = "rediss://"
        _redis_tls_requirements = f"?ssl_cert_reqs={CONFIG.get('redis.tls_reqs')}"
        if _redis_ca := CONFIG.get("redis.tls_ca_cert", None):
            _redis_tls_requirements += f"&ssl_ca_certs={_redis_ca}"
    _redis_url = (
        f"{_redis_protocol_prefix}"
        f"{quote_plus(CONFIG.get('redis.username'))}:"
        f"{quote_plus(CONFIG.get('redis.password'))}@"
        f"{quote_plus(CONFIG.get('redis.host'))}:"
        f"{CONFIG.get_int('redis.port')}"
        f"/{db}{_redis_tls_requirements}"
    )
    return _redis_url


def django_db_config(config: ConfigLoader | None = None) -> dict:
    if not config:
        config = CONFIG
    db = {
        "default": {
            "ENGINE": "authentik.root.db",
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
            },
            "CONN_MAX_AGE": CONFIG.get_optional_int("postgresql.conn_max_age", 0),
            "CONN_HEALTH_CHECKS": CONFIG.get_bool("postgresql.conn_health_checks", False),
            "DISABLE_SERVER_SIDE_CURSORS": CONFIG.get_bool(
                "postgresql.disable_server_side_cursors", False
            ),
            "TEST": {
                "NAME": config.get("postgresql.test.name"),
            },
        }
    }

    conn_max_age = CONFIG.get_optional_int("postgresql.conn_max_age", UNSET)
    disable_server_side_cursors = CONFIG.get_bool("postgresql.disable_server_side_cursors", UNSET)
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
        for setting in db["default"]["OPTIONS"].keys():
            override = config.get(
                f"postgresql.read_replicas.{replica}.{setting.lower()}", default=UNSET
            )
            if override is not UNSET:
                _database["OPTIONS"][setting] = override
        db[f"replica_{replica}"] = _database
    return db


if __name__ == "__main__":
    if len(argv) < 2:  # noqa: PLR2004
        print(dumps(CONFIG.raw, indent=4, cls=AttrEncoder))
    else:
        print(CONFIG.get(argv[-1]))
