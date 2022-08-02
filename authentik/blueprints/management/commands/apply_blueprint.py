"""Apply blueprint from commandline"""
from django.core.management.base import BaseCommand, no_translations
from structlog.stdlib import get_logger

from authentik.blueprints.v1.importer import Importer

LOGGER = get_logger()


class Command(BaseCommand):
    """Apply blueprint from commandline"""

    @no_translations
    def handle(self, *args, **options):
        """Apply all blueprints in order, abort when one fails to import"""
        for blueprint_path in options.get("blueprints", []):
            with open(blueprint_path, "r", encoding="utf8") as blueprint_file:
                importer = Importer(blueprint_file.read())
                valid, logs = importer.validate()
                if not valid:
                    for log in logs:
                        LOGGER.debug(**log)
                    raise ValueError("blueprint invalid")
                importer.apply()

    def add_arguments(self, parser):
        parser.add_argument("blueprints", nargs="+", type=str)
