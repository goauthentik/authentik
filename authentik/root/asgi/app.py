"""
ASGI config for authentik project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""
import django
from asgiref.compatibility import guarantee_single_callable
from channels.routing import ProtocolTypeRouter, URLRouter
from defusedxml import defuse_stdlib
from django.core.asgi import get_asgi_application
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from authentik.root.asgi.error_handler import ASGIErrorHandler
from authentik.root.asgi.logger import ASGILogger

# DJANGO_SETTINGS_MODULE is set in gunicorn.conf.py

defuse_stdlib()
django.setup()

# pylint: disable=wrong-import-position
from authentik.root import websocket  # noqa  # isort:skip

application = ASGIErrorHandler(
    ASGILogger(
        guarantee_single_callable(
            SentryAsgiMiddleware(
                ProtocolTypeRouter(
                    {
                        "http": get_asgi_application(),
                        "websocket": URLRouter(websocket.websocket_urlpatterns),
                    }
                )
            )
        )
    )
)
