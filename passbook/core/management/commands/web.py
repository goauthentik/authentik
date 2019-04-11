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
        """passbook cherrypy server"""
        autoreload.run_with_reloader(self.daphne_server)

    def daphne_server(self):
        """Run daphne server within autoreload"""
        autoreload.raise_last_exception()
        with CONFIG.cd('web'):
            CommandLineInterface().run([
                '-p', str(CONFIG.get('port', 8000)),
                '-b', CONFIG.get('listen', '0.0.0.0'),  # nosec
                '--access-log', '/dev/null',
                'passbook.core.asgi:application'
            ])
