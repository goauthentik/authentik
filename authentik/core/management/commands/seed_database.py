"""Seed development databases with core objects."""

from argparse import ArgumentParser
from random import Random

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import CommandError

from authentik.core.management.seed_database.config import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_PASSWORD,
    DEFAULT_PREFIX,
    SIZE_PRESETS,
    STATIC_SEED,
    resolve_seed_size,
    validate_seed_size,
)
from authentik.core.management.seed_database.names import SeedNamer, seed_prefix
from authentik.core.management.seed_database.progress import SeedProgress
from authentik.core.management.seed_database.seeder import SEED_PHASES, DatabaseSeeder
from authentik.tenants.management import TenantCommand


class Command(TenantCommand):
    """Seed a development database with core data."""

    help = (
        "Seed a development database with users, groups, applications, and providers. "
        "Requires DEBUG or TEST and an explicit risk acknowledgement."
    )

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--ack-risk",
            action="store_true",
            help="Acknowledge that this command creates many database rows.",
        )
        parser.add_argument(
            "--size",
            choices=SIZE_PRESETS.keys(),
            default="s",
            type=str.lower,
            help="Seed size preset.",
        )
        parser.add_argument(
            "--mode",
            choices=["static", "random"],
            default="static",
            help="Generate repeatable static data or randomized data.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Seed used for random mode. Static mode always uses a stable seed.",
        )
        parser.add_argument(
            "--prefix",
            default=DEFAULT_PREFIX,
            help="Prefix for generated usernames and group names.",
        )
        parser.add_argument(
            "--password",
            default=DEFAULT_PASSWORD,
            help="Password assigned to generated users.",
        )
        parser.add_argument("--users", type=int, default=None, help="Override user count.")
        parser.add_argument("--groups", type=int, default=None, help="Override group count.")
        parser.add_argument(
            "--superuser-groups",
            type=int,
            default=None,
            help="Override the number of generated superuser groups.",
        )
        parser.add_argument(
            "--memberships-per-user",
            type=int,
            default=None,
            help="Override generated memberships per user.",
        )
        parser.add_argument(
            "--apps",
            type=int,
            default=None,
            help="Override generated application and OAuth2 provider count.",
        )
        parser.add_argument(
            "--entitlements-per-app",
            type=int,
            default=None,
            help="Override generated application entitlements per application.",
        )
        parser.add_argument(
            "--app-group-bindings-per-app",
            type=int,
            default=None,
            help="Override generated group policy bindings per application.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=DEFAULT_BATCH_SIZE,
            help="Batch size for bulk database writes.",
        )
        parser.add_argument(
            "--no-progress",
            action="store_true",
            help="Disable progress output.",
        )

    def handle_per_tenant(self, *args, **options):
        """Seed users, groups, applications, providers, and memberships for the selected tenant."""
        if not options["ack_risk"]:
            raise CommandError("Pass --ack-risk to acknowledge that this command creates data.")
        if not settings.DEBUG and not getattr(settings, "TEST", False):
            raise CommandError("This command can only run with DEBUG or TEST enabled.")

        size = resolve_seed_size(options)
        mode = options["mode"]
        seed = STATIC_SEED if mode == "static" else options["seed"]
        rng = Random(seed)  # nosec B311
        namer = SeedNamer(seed_prefix(options["prefix"], mode, rng))
        password_hash = make_password(options["password"], salt="authentik_seed")
        batch_size = options["batch_size"]
        validate_seed_size(size, namer, batch_size)

        result = DatabaseSeeder(
            size=size,
            namer=namer,
            mode=mode,
            rng=rng,
            password_hash=password_hash,
            batch_size=batch_size,
            progress=SeedProgress(
                self.stdout,
                SEED_PHASES,
                enabled=not options["no_progress"] and int(options.get("verbosity", 1)) > 0,
            ),
        ).seed()
        self.stdout.write(self.style.SUCCESS(result.message()))
