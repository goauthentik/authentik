"""root Websocket URLS"""
from channels.auth import AuthMiddlewareStack
from django.urls import path

from authentik.core.ws.consumer import FrontendConsumer
from authentik.lib.sentry import SentryWSMiddleware
from authentik.outposts.channels import OutpostConsumer

websocket_urlpatterns = [
    path("ws/outpost/<uuid:pk>/", SentryWSMiddleware(OutpostConsumer.as_asgi())),
    path("ws/client/", AuthMiddlewareStack(SentryWSMiddleware(FrontendConsumer.as_asgi()))),
]
