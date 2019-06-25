"""
WSGI config for passbook project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'passbook.settings')

application = SentryWsgiMiddleware(get_wsgi_application())
