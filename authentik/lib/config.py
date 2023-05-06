"""authentik core config loader"""
import os
from collections.abc import Mapping
from contextlib import contextmanager
from glob import glob
from json import dumps, loads
from json.decoder import JSONDecodeError
from sys import argv, stderr
from time import time
from typing import Any
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse

import yaml
from django.conf import ImproperlyConfigured

SEARCH_PATHS = ["authentik/lib/default.yml", "/etc/authentik/config.yml", ""] + glob(
    "/etc/authentik/config.d/*.yml", recursive=True
)
ENV_PREFIX = "AUTHENTIK"
ENVIRONMENT = os.getenv(f"{ENV_PREFIX}_ENV", "local")

DEPRECATIONS = {
    "redis.broker_url": "broker.url",
    "redis.broker_transport_options": "broker.transport_options",
    "redis.cache_timeout": "cache.timeout",
    "redis.cache_timeout_flows": "cache.timeout_flows",
    "redis.cache_timeout_policies": "cache.timeout_policies",
    "redis.cache_timeout_reputation": "cache.timeout_reputation",
}


def get_path_from_dict(root: dict, path: str, sep=".", default=None) -> Any:
    """Recursively walk through `root`, checking each part of `path` split by `sep`.
    If at any point a dict does not exist, return default"""
    for comp in path.split(sep):
        if root and comp in root:
            root = root.get(comp)
        else:
            return default
    return root


class UNSET:
    """Used to test whether configuration key has not been set."""


class ConfigLoader:
    """Search through SEARCH_PATHS and load configuration. Environment variables starting with
    `ENV_PREFIX` are also applied.

    A variable like AUTHENTIK_POSTGRESQL__HOST would translate to postgresql.host"""

    loaded_file = []

    def __init__(self):
        super().__init__()
        self.__config = {}
        base_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "../.."))
        for path in SEARCH_PATHS:
            # Check if path is relative, and if so join with base_dir
            if not os.path.isabs(path):
                path = os.path.join(base_dir, path)
            if os.path.isfile(path) and os.path.exists(path):
                # Path is an existing file, so we just read it and update our config with it
                self.update_from_file(path)
            elif os.path.isdir(path) and os.path.exists(path):
                # Path is an existing dir, so we try to read the env config from it
                env_paths = [
                    os.path.join(path, ENVIRONMENT + ".yml"),
                    os.path.join(path, ENVIRONMENT + ".env.yml"),
                ]
                for env_file in env_paths:
                    if os.path.isfile(env_file) and os.path.exists(env_file):
                        # Update config with env file
                        self.update_from_file(env_file)
        self.update_from_env()
        self.check_deprecations()
        self.update_redis_url_from_env()

    def update_redis_url_from_env(self):
        """Build Redis URL from other env variables"""

        redis_url = "redis://"
        redis_url_query = {}
        redis_host = "localhost"
        redis_port = 6379
        redis_db = 0

        if self.y("redis.url", UNSET) is not UNSET:
            redis_url_old = urlparse(self.y("redis.url"))
            redis_url_query = dict(parse_qsl(redis_url_old.query))
            redis_host = redis_url_old.hostname
            redis_port = redis_url_old.port
            if redis_url_old.path[1:].isdigit():
                redis_db = redis_url_old.path[1:]
            if self.y("redis.tls", UNSET) is UNSET:
                redis_url = redis_url_old.scheme
        if self.y_bool("redis.tls", False):
            redis_url = "rediss://"
        if self.y("redis.tls_reqs", UNSET) is not UNSET:
            redis_tls_reqs = self.y("redis.tls_reqs")
            match redis_tls_reqs.lower():
                case "none":
                    redis_url_query.pop("skipverify", None)
                    redis_url_query["insecureskipverify"] = "true"
                case "optional":
                    redis_url_query.pop("insecureskipverify", None)
                    redis_url_query["skipverify"] = "true"
                case "required":
                    pass
                case _:
                    self.log(
                        "warning",
                        f"Unsupported Redis TLS requirements option '{redis_tls_reqs}'! "
                        "Using default option 'required'.",
                    )
        if self.y("redis.db", UNSET) is not UNSET:
            redis_db = int(self.y("redis.db"))
        if self.y("redis.host", UNSET) is not UNSET:
            redis_host = self.y("redis.host")
        if self.y("redis.port", UNSET) is not UNSET:
            redis_port = int(self.y("redis.port"))
        if self.y("redis.username", UNSET) is not UNSET:
            redis_url_query["username"] = self.y("redis.username")
        if self.y("redis.password", UNSET) is not UNSET:
            redis_url_query["password"] = self.y("redis.password")
        redis_url += f"{quote_plus(redis_host)}"
        redis_url += f":{redis_port}"
        redis_url += f"/{redis_db}"
        # Sort query to have similar tests between Go and Python implementation
        redis_url_query = dict(sorted(redis_url_query.items()))
        redis_url_query = urlencode(redis_url_query)
        if redis_url_query != "":
            redis_url += f"?{redis_url_query}"
        self.y_set("redis.url", redis_url)

    def check_deprecations(self):
        """Warn if any deprecated configuration options are used"""

        def _pop_deprecated_key(current_obj, dot_parts, index):
            """Recursive function to remove deprecated keys in configuration"""
            dot_part = dot_parts[index]
            if dot_part in current_obj:
                if index == len(dot_parts) - 1:
                    return current_obj.pop(dot_part)
                value = _pop_deprecated_key(current_obj[dot_part], dot_parts, index + 1)
                if not current_obj[dot_part]:
                    current_obj.pop(dot_part)
                return value
            return None

        for deprecation, replacement in DEPRECATIONS.items():
            if self.y(deprecation, default=UNSET) is not UNSET:
                self.log(
                    "warning",
                    f"'{deprecation}' has been deprecated in favor of '{replacement}'! "
                    "Please update your configuration.",
                )

                deprecated_value = _pop_deprecated_key(self.__config, deprecation.split("."), 0)
                self.y_set(replacement, deprecated_value)

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
        for key, value in updatee.items():
            if isinstance(value, Mapping):
                root[key] = self.update(root.get(key, {}), value)
            else:
                if isinstance(value, str):
                    value = self.parse_uri(value)
                root[key] = value
        return root

    def parse_uri(self, value: str) -> str:
        """Parse string values which start with a URI"""
        url = urlparse(value)
        if url.scheme == "env":
            value = os.getenv(url.netloc, url.query)
        if url.scheme == "file":
            try:
                with open(url.path, "r", encoding="utf8") as _file:
                    value = _file.read().strip()
            except OSError as exc:
                self.log("error", f"Failed to read config value from {url.path}: {exc}")
                value = url.query
        return value

    def update_from_file(self, path: str):
        """Update config from file contents"""
        try:
            with open(path, encoding="utf8") as file:
                try:
                    self.update(self.__config, yaml.safe_load(file))
                    self.log("debug", "Loaded config", file=path)
                    self.loaded_file.append(path)
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

    @staticmethod
    def _set_value_for_key_path(outer, path, value, sep="."):
        # Recursively convert path from a.b.c into outer[a][b][c]
        current_obj = outer
        dot_parts = path.split(sep)
        for dot_part in dot_parts[:-1]:
            current_obj.setdefault(dot_part, {})
            current_obj = current_obj[dot_part]
        current_obj[dot_parts[-1]] = value
        return outer

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
                value = loads(value)
            except JSONDecodeError:
                pass
            outer = self._set_value_for_key_path(outer, relative_key, value)
            idx += 1
        if idx > 0:
            self.log("debug", "Loaded environment variables", count=idx)
            self.update(self.__config, outer)

    @contextmanager
    def patch(self, path: str, value: Any):
        """Context manager for unittests to patch a value"""
        original_value = self.y(path)
        self.y_set(path, value)
        try:
            yield
        finally:
            self.y_set(path, original_value)

    @property
    def raw(self) -> dict:
        """Get raw config dictionary"""
        return self.__config

    # pylint: disable=invalid-name
    def y(self, path: str, default=None, sep=".") -> Any:
        """Access attribute by using yaml path"""
        # Walk sub_dicts before parsing path
        root = self.raw
        # Walk each component of the path
        return get_path_from_dict(root, path, sep=sep, default=default)

    def y_set(self, path: str, value: Any, sep="."):
        """Set value using same syntax as y()"""
        # Walk sub_dicts before parsing path
        self._set_value_for_key_path(self.raw, path, value, sep)

    def y_bool(self, path: str, default=False) -> bool:
        """Wrapper for y that converts value into boolean"""
        return str(self.y(path, default)).lower() == "true"


CONFIG = ConfigLoader()

if __name__ == "__main__":
    if len(argv) < 2:
        print(dumps(CONFIG.raw, indent=4))
    else:
        print(CONFIG.y(argv[1]))
