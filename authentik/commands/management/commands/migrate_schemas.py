from django_tenants.management.commands.migrate_schemas import Command as BaseCommand

from authentik.commands.management.commands import MigrationAutodetector


class Command(BaseCommand):
    autodetector = MigrationAutodetector
