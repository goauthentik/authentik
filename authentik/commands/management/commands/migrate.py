from django_tenants.management.commands.migrate import Command as BaseCommand

from authentik.commands.management.commands import MigrationAutodetector


class Command(BaseCommand):
    autodetector = MigrationAutodetector  # type: ignore[assignment]
