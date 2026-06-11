"""Progress reporting for development database seeding."""

from dataclasses import dataclass
from typing import Protocol


class ProgressWriter(Protocol):
    """Small subset of Django's OutputWrapper used by the progress reporter."""

    def write(self, msg: str = "", style_func=None, ending: str | None = None): ...


@dataclass
class SeedProgress:
    """Render phase progress for seed operations."""

    writer: ProgressWriter
    total: int
    enabled: bool = True
    width: int = 24

    def update(self, current: int, label: str):
        """Write progress for the current phase."""
        if not self.enabled:
            return
        filled = int(self.width * current // self.total)
        bar = "#" * filled + "-" * (self.width - filled)
        self.writer.write(f"Seeding |{bar}| {current}/{self.total} {label}")
