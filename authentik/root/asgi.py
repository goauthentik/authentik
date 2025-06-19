"""
ASGI config for authentik project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from authentik.root.setup import setup

# DJANGO_SETTINGS_MODULE is set in gunicorn.conf.py

setup()
django.setup()


from authentik.root import websocket  # noqa


class LifespanApp:
    """
    temporary shim for https://github.com/django/channels/issues/1216
    needed so that hypercorn doesn't display an error.
    this uses ASGI 2.0 format, not the newer 3.0 single callable
    """

    def __init__(self, scope):
        self.scope = scope

    async def __call__(self, receive, send):
        if self.scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return


class RouteNotFoundMiddleware:
    """Middleware to ignore 404s for websocket requests
    taken from https://github.com/django/daphne/issues/165#issuecomment-808284950"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            return await self.app(scope, receive, send)
        except ValueError as exc:
            if "No route found for path" in str(exc) and scope["type"] == "websocket":
                await send({"type": "websocket.close"})
            else:
                raise exc


class AuthentikAsgi(SentryAsgiMiddleware):
    """Root ASGI App wrapper"""

    def call_startup(self):
        from authentik.root.signals import post_startup, pre_startup, startup

        pre_startup.send(sender=self)
        startup.send(sender=self)
        post_startup.send(sender=self)


application = AuthentikAsgi(
    ProtocolTypeRouter(
        {
            "http": get_asgi_application(),
            "websocket": RouteNotFoundMiddleware(URLRouter(websocket.websocket_urlpatterns)),
            "lifespan": LifespanApp,
        }
    )
)
