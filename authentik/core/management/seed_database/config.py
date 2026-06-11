"""Configuration for development database seeding."""

from dataclasses import dataclass
from typing import Any

from django.core.management.base import CommandError

from authentik.core.management.seed_database.names import SeedNamer
from authentik.core.models import USERNAME_MAX_LENGTH

STATIC_SEED = 1
DEFAULT_PREFIX = "ak-seed"
DEFAULT_PASSWORD = "ak-seed-password"  # nosec
DEFAULT_BATCH_SIZE = 1_000


@dataclass(frozen=True)
class SeedSize:
    """Counts for a seed size preset."""

    users: int
    groups: int
    superuser_groups: int
    memberships_per_user: int
    apps: int
    entitlements_per_app: int
    app_group_bindings_per_app: int


SIZE_PRESETS = {
    "s": SeedSize(
        users=25,
        groups=5,
        superuser_groups=1,
        memberships_per_user=2,
        apps=5,
        entitlements_per_app=2,
        app_group_bindings_per_app=2,
    ),
    "m": SeedSize(
        users=250,
        groups=25,
        superuser_groups=2,
        memberships_per_user=3,
        apps=25,
        entitlements_per_app=3,
        app_group_bindings_per_app=3,
    ),
    "l": SeedSize(
        users=1_000,
        groups=100,
        superuser_groups=5,
        memberships_per_user=5,
        apps=100,
        entitlements_per_app=5,
        app_group_bindings_per_app=5,
    ),
    "xl": SeedSize(
        users=10_000,
        groups=500,
        superuser_groups=10,
        memberships_per_user=8,
        apps=250,
        entitlements_per_app=8,
        app_group_bindings_per_app=8,
    ),
}


def resolve_seed_size(options: dict[str, Any]) -> SeedSize:
    """Resolve a size preset with any explicit CLI count overrides."""
    preset = SIZE_PRESETS[options["size"]]
    return SeedSize(
        users=options["users"] if options["users"] is not None else preset.users,
        groups=options["groups"] if options["groups"] is not None else preset.groups,
        superuser_groups=(
            options["superuser_groups"]
            if options["superuser_groups"] is not None
            else preset.superuser_groups
        ),
        memberships_per_user=(
            options["memberships_per_user"]
            if options["memberships_per_user"] is not None
            else preset.memberships_per_user
        ),
        apps=options["apps"] if options["apps"] is not None else preset.apps,
        entitlements_per_app=(
            options["entitlements_per_app"]
            if options["entitlements_per_app"] is not None
            else preset.entitlements_per_app
        ),
        app_group_bindings_per_app=(
            options["app_group_bindings_per_app"]
            if options["app_group_bindings_per_app"] is not None
            else preset.app_group_bindings_per_app
        ),
    )


def validate_seed_size(size: SeedSize, namer: SeedNamer, batch_size: int):
    """Validate requested seed counts before writing any rows."""
    if size.users < 1:
        raise CommandError("User count must be at least 1.")
    if size.groups < 1:
        raise CommandError("Group count must be at least 1.")
    if size.superuser_groups < 0:
        raise CommandError("Superuser group count cannot be negative.")
    if size.superuser_groups > size.groups:
        raise CommandError("Superuser group count cannot be greater than group count.")
    if size.memberships_per_user < 0:
        raise CommandError("Memberships per user cannot be negative.")
    if size.memberships_per_user > size.groups:
        raise CommandError("Memberships per user cannot be greater than group count.")
    if size.apps < 0:
        raise CommandError("Application count cannot be negative.")
    if size.entitlements_per_app < 0:
        raise CommandError("Entitlements per application cannot be negative.")
    if size.app_group_bindings_per_app < 0:
        raise CommandError("Application group bindings per application cannot be negative.")
    if size.app_group_bindings_per_app > size.groups:
        raise CommandError(
            "Application group bindings per application cannot be greater than group count."
        )
    if batch_size < 1:
        raise CommandError("Batch size must be at least 1.")

    username = namer.username(size.users - 1)
    if len(username) > USERNAME_MAX_LENGTH:
        raise CommandError(
            f"Prefix is too long. Longest generated username would be {len(username)} "
            f"characters, but the limit is {USERNAME_MAX_LENGTH}."
        )
