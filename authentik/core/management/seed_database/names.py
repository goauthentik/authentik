"""Name helpers for development seed data."""

from dataclasses import dataclass
from random import Random

from authentik.core.models import USER_PATH_SYSTEM_PREFIX

SEED_ATTRIBUTE = f"{USER_PATH_SYSTEM_PREFIX}/seed"


def seed_prefix(prefix: str, mode: str, rng: Random) -> str:
    """Return the static prefix or a randomized run-specific prefix."""
    if mode == "static":
        return prefix
    run_id = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(8))
    return f"{prefix}-{run_id}"


@dataclass(frozen=True)
class SeedNamer:
    """Generate consistent seed object names from a prefix."""

    prefix: str

    def attributes(self, mode: str, index: int) -> dict:
        """Return the common seed marker used by models with attributes."""
        return {
            SEED_ATTRIBUTE: {
                "command": "seed_database",
                "mode": mode,
                "index": index,
            },
        }

    def username(self, index: int) -> str:
        return f"{self.prefix}-user-{index + 1:06d}"

    def group_name(self, index: int) -> str:
        return f"{self.prefix}-group-{index + 1:04d}"

    def provider_name(self, index: int) -> str:
        return f"{self.prefix}-provider-{index + 1:04d}"

    def application_slug(self, index: int) -> str:
        return f"{self.prefix}-app-{index + 1:04d}"

    def entitlement_name(self, index: int) -> str:
        return f"{self.prefix}-entitlement-{index + 1:04d}"
