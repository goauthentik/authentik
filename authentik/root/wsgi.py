"""WSGI config for authentik project.

Ordinary HTTP requests are served through this, on whichever thread the embedding
Rust binary happens to run them on. Websockets still go through ``authentik.root.asgi``,
since WSGI has no notion of them.
"""

import django
from django.core.wsgi import get_wsgi_application
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware

from authentik.root.setup import setup

# DJANGO_SETTINGS_MODULE is set in lifecycle/server.py

setup()
django.setup()

application = SentryWsgiMiddleware(get_wsgi_application())
