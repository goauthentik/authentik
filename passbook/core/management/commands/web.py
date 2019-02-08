"""passbook Webserver management command"""

from logging import getLogger

import cherrypy
from django.conf import settings
from django.core.management.base import BaseCommand

from passbook.core.wsgi import application

LOGGER = getLogger(__name__)


class Command(BaseCommand):
    """Run CherryPy webserver"""

    def handle(self, *args, **options):
        """passbook cherrypy server"""
        config = settings.CHERRYPY_SERVER
        config.update(**options)
        cherrypy.config.update(config)
        cherrypy.tree.graft(application, '/')
        # Mount NullObject to serve static files
        cherrypy.tree.mount(None, '/static', config={
            '/': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': settings.STATIC_ROOT,
                'tools.expires.on': True,
                'tools.expires.secs': 86400,
                'tools.gzip.on': True,
            }
        })
        cherrypy.engine.start()
        cherrypy.engine.block()
