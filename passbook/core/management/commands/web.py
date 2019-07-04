"""passbook Webserver management command"""

from logging import getLogger

import cherrypy
from django.conf import settings
from django.core.management.base import BaseCommand

from passbook.lib.config import CONFIG
from passbook.root.wsgi import application

LOGGER = getLogger(__name__)


class Command(BaseCommand):
    """Run CherryPy webserver"""

    def handle(self, *args, **options):
        """passbook cherrypy server"""
        cherrypy.config.update(CONFIG.get('web'))
        cherrypy.tree.graft(application, '/')
        # Mount NullObject to serve static files
        cherrypy.tree.mount(None, settings.STATIC_URL, config={
            '/': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': settings.STATIC_ROOT,
                'tools.expires.on': True,
                'tools.expires.secs': 86400,
                'tools.gzip.on': True,
            }
        })
        cherrypy.engine.start()
        for file in CONFIG.loaded_file:
            cherrypy.engine.autoreload.files.add(file)
            LOGGER.info("Added '%s' to autoreload triggers", file)
        cherrypy.engine.block()
