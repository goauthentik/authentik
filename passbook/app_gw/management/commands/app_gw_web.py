"""passbook app_gw webserver management command"""

from daphne.cli import CommandLineInterface
from django.core.management.base import BaseCommand
from django.utils import autoreload
from structlog import get_logger

from passbook.lib.config import CONFIG

LOGGER = get_logger(__name__)


class Command(BaseCommand):
    """Run Daphne Webserver for app_gw"""

    def handle(self, *args, **options):
        """passbook daphne server"""
        autoreload.run_with_reloader(self.daphne_server)

    def daphne_server(self):
        """Run daphne server within autoreload"""
        autoreload.raise_last_exception()
        CommandLineInterface().run([
            '-p', str(CONFIG.y('app_gw.port', 8000)),
            '-b', CONFIG.y('app_gw.listen', '0.0.0.0'),  # nosec
            '--access-log', '/dev/null',
            '--application-close-timeout', '500',
            'passbook.app_gw.asgi:application'
        ])
