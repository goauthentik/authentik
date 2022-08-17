"""Export blueprint of current authentik install"""
from django.core.management.base import BaseCommand, no_translations
from structlog.stdlib import get_logger

from authentik.blueprints.v1.exporter import Exporter

LOGGER = get_logger()


class Command(BaseCommand):
    """Export blueprint of current authentik install"""

    @no_translations
    def handle(self, *args, **options):
        """Export blueprint of current authentik install"""
        exporter = Exporter()
        self.stdout.write(exporter.export_to_string())
