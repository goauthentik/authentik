"""State for config files"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from json import loads
from typing import Optional

from django.core.cache import cache


class FileStatus(Enum):
    """Status that a config file can have."""

    UNKNOWN = 1
    APPLIED_SUCCESSFULLY = 2
    FAILED_TO_APPLY = 4


@dataclass
class ConfigFile:
    """State of a single config file"""

    path: str
    status: FileStatus = field(default=FileStatus.UNKNOWN)
    last_applied: datetime = field(default=datetime.now())
    message: str = field(default="")

    content: dict = field(default_factory=dict)

    def __init__(self, path: str) -> None:
        self.path = path
        self._load()

    def _load(self):
        try:
            with open(self.path, "r+", encoding="utf-8") as _file:
                self.content = loads(_file.read())
        except IOError as exc:
            self.status = FileStatus.FAILED_TO_APPLY
            self.message = str(exc)

    @staticmethod
    def all() -> dict[str, "ConfigFile"]:
        """Get all ConfigFile objects"""
        return cache.get_many(cache.keys("config_file_*"))

    @staticmethod
    def by_path(path: str) -> Optional["ConfigFile"]:
        """Get ConfigFile Object by path"""
        return cache.get(f"config_file_{path}")

    def delete(self):
        """Delete config info from cache"""
        return cache.delete(f"config_file_{self.path}")

    def save(self, timeout_hours=6):
        """Save config into cache"""
        key = f"config_file_{self.path}"
        cache.set(key, self, timeout=timeout_hours * 60 * 60)
