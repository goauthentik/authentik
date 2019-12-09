"""
WSGI config for passbook project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""
import os
from time import time

from django.core.wsgi import get_wsgi_application
from structlog import get_logger

from passbook.lib.utils.http import _get_client_ip_from_meta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "passbook.root.settings")

class WSGILogger:
    """ This is the generalized WSGI middleware for any style request logging. """

    def __init__(self, application):
        self.application = application
        self.logger = get_logger('passbook.wsgi')

    def __healthcheck(self, start_response):
        start_response('204 OK', [])
        return [b'']

    def __call__(self, environ, start_response):
        start = time()
        status_codes = []
        content_lengths = []

        if environ.get('HTTP_HOST', '').startswith('kubernetes-healthcheck-host'):
            # Don't log kubernetes health/readiness requests
            return self.__healthcheck(start_response)

        def custom_start_response(status, response_headers, exc_info=None):
            status_codes.append(int(status.partition(' ')[0]))
            for name, value in response_headers:
                if name.lower() == 'content-length':
                    content_lengths.append(int(value))
                    break
            return start_response(status, response_headers, exc_info)
        retval = self.application(environ, custom_start_response)
        runtime = int((time() - start) * 10**6)
        content_length = content_lengths[0] if content_lengths else 0
        self.log(status_codes[0], environ, content_length, runtime=runtime)
        return retval

    def log(self, status_code, environ, content_length, **kwargs):
        """
        Apache log format 'NCSA extended/combined log':
        "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\""
        see http://httpd.apache.org/docs/current/mod/mod_log_config.html#formats
        """
        host = _get_client_ip_from_meta(environ)
        query_string = ''
        if environ.get('QUERY_STRING') != '':
            query_string = f"?{environ.get('QUERY_STRING')}"
        self.logger.info(f"{environ.get('PATH_INFO', '')}{query_string}",
                         host=host,
                         method=environ.get('REQUEST_METHOD', ''),
                         protocol=environ.get('SERVER_PROTOCOL', ''),
                         status=status_code,
                         size=content_length / 1000 if content_length > 0 else '-',
                         runtime=kwargs.get('runtime'))


application = WSGILogger(get_wsgi_application())
