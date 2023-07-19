"""authentik core config loader"""
import os
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from glob import glob
from json import JSONEncoder, dumps, loads
from json.decoder import JSONDecodeError
from pathlib import Path
from sys import argv, stderr
from time import time
from typing import Any, Optional
from urllib.parse import urlparse

import yaml
from django.conf import ImproperlyConfigured

SEARCH_PATHS = ["authentik/lib/default.yml", "/etc/authentik/config.yml", ""] + glob(
    "/etc/authentik/config.d/*.yml", recursive=True
)
ENV_PREFIX = "AUTHENTIK"
ENVIRONMENT = os.getenv(f"{ENV_PREFIX}_ENV", "local")


def get_path_from_dict(root: dict, path: str, sep=".", default=None) -> Any:
    """Recursively walk through `root`, checking each part of `path` split by `sep`.
    If at any point a dict does not exist, return default"""
    for comp in path.split(sep):
        if root and comp in root:
            root = root.get(comp)
        else:
            return default
    return root


@dataclass
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
    source: Optional[str] = field(default=None)


class AttrEncoder(JSONEncoder):
    """JSON encoder that can deal with `Attr` classes"""

    def default(self, o: Any) -> Any:
        if isinstance(o, Attr):
            return o.value
        return super().default(o)


class ConfigLoader:
    """Search through SEARCH_PATHS and load configuration. Environment variables starting with
    `ENV_PREFIX` are also applied.

    A variable like AUTHENTIK_POSTGRESQL__HOST would translate to postgresql.host"""

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
                elif isinstance(value, Attr) and isinstance(value.value, str):
                    value = self.parse_uri(value.value)
                elif not isinstance(value, Attr):
                    value = Attr(value)
                root[key] = value
        return root

    def refresh(self, key: str):
        """Update a single value"""
        attr: Attr = get_path_from_dict(self.raw, key)
        if attr.source_type != Attr.Source.URI:
            return
        attr.value = self.parse_uri(attr.source).value

    def parse_uri(self, value: str) -> Attr:
        """Parse string values which start with a URI"""
        url = urlparse(value)
        parsed_value = value
        if url.scheme == "env":
            parsed_value = os.getenv(url.netloc, url.query)
        if url.scheme == "file":
            try:
                with open(url.path, "r", encoding="utf8") as _file:
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

    def update_from_env(self):
        """Check environment variables"""
        outer = {}
        idx = 0
        for key, value in os.environ.items():
            if not key.startswith(ENV_PREFIX):
                continue
            relative_key = key.replace(f"{ENV_PREFIX}_", "", 1).replace("__", ".").lower()
            # Recursively convert path from a.b.c into outer[a][b][c]
            current_obj = outer
            dot_parts = relative_key.split(".")
            for dot_part in dot_parts[:-1]:
                if dot_part not in current_obj:
                    current_obj[dot_part] = {}
                current_obj = current_obj[dot_part]
            # Check if the value is json, and try to load it
            try:
                value = loads(value)
            except JSONDecodeError:
                pass
            current_obj[dot_parts[-1]] = Attr(value, Attr.Source.ENV, key)
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

    def get_bool(self, path: str, default=False) -> bool:
        """Wrapper for get that converts value into boolean"""
        return str(self.get(path, default)).lower() == "true"

    def set(self, path: str, value: Any, sep="."):
        """Set value using same syntax as get()"""
        # Walk sub_dicts before parsing path
        root = self.raw
        # Walk each component of the path
        path_parts = path.split(sep)
        for comp in path_parts[:-1]:
            if comp not in root:
                root[comp] = {}
            root = root.get(comp, {})
        root[path_parts[-1]] = Attr(value)


CONFIG = ConfigLoader()


if __name__ == "__main__":
    if len(argv) < 2:
        print(dumps(CONFIG.raw, indent=4, cls=AttrEncoder))
    else:
        print(CONFIG.get(argv[1]))
