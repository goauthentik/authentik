from django.core.management.commands.makemigrations import Command as BaseCommand

from authentik.commands.management.commands import MigrationAutodetector


class Command(BaseCommand):
    autodetector = MigrationAutodetector
