"""passbook Webserver management command"""

from logging import getLogger

from daphne.cli import CommandLineInterface
from django.core.management.base import BaseCommand
from django.utils import autoreload

from passbook.lib.config import CONFIG

LOGGER = getLogger(__name__)


class Command(BaseCommand):
    """Run CherryPy webserver"""

    def handle(self, *args, **options):
        """passbook daphne server"""
        autoreload.run_with_reloader(self.daphne_server)

    def daphne_server(self):
        """Run daphne server within autoreload"""
        autoreload.raise_last_exception()
        CommandLineInterface().run([
            '-p', str(CONFIG.y('web.port', 8000)),
            '-b', CONFIG.y('web.listen', '0.0.0.0'),  # nosec
            '--access-log', '/dev/null',
            '--application-close-timeout', '500',
            'passbook.root.asgi:application'
        ])
