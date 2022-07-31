"""Apply blueprint from commandline"""
from django.core.management.base import BaseCommand, no_translations

from authentik.blueprints.v1.importer import Importer


class Command(BaseCommand):  # pragma: no cover
    """Apply blueprint from commandline"""

    @no_translations
    def handle(self, *args, **options):
        """Apply all blueprints in order, abort when one fails to import"""
        for blueprint_path in options.get("blueprints", []):
            with open(blueprint_path, "r", encoding="utf8") as blueprint_file:
                importer = Importer(blueprint_file.read())
                valid = importer.validate()
                if not valid:
                    raise ValueError("blueprint invalid")
                importer.apply()

    def add_arguments(self, parser):
        parser.add_argument("blueprints", nargs="+", type=str)
