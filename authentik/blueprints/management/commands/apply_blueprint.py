"""Apply blueprint from commandline"""
from sys import exit as sys_exit

from django.core.management.base import BaseCommand, no_translations
from structlog.stdlib import get_logger

from authentik.blueprints.models import BlueprintInstance
from authentik.blueprints.v1.importer import Importer

LOGGER = get_logger()


class Command(BaseCommand):
    """Apply blueprint from commandline"""

    @no_translations
    def handle(self, *args, **options):
        """Apply all blueprints in order, abort when one fails to import"""
        for blueprint_path in options.get("blueprints", []):
            content = BlueprintInstance(path=blueprint_path).retrieve()
            importer = Importer.from_string(content)
            valid, _ = importer.validate()
            if not valid:
                self.stderr.write("blueprint invalid")
                sys_exit(1)
            importer.apply()

    def add_arguments(self, parser):
        parser.add_argument("blueprints", nargs="+", type=str)
