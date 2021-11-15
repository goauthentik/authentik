"""Output full config"""
from json import dumps

from django.core.management.base import BaseCommand, no_translations

from authentik.lib.config import CONFIG


class Command(BaseCommand):  # pragma: no cover
    """Output full config"""

    @no_translations
    def handle(self, *args, **options):
        """Check permissions for all apps"""
        print(dumps(CONFIG.raw, indent=4))
