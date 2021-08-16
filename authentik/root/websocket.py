"""root Websocket URLS"""
from channels.auth import AuthMiddlewareStack
from django.urls import path

from authentik.lib.sentry import SentryWSMiddleware
from authentik.outposts.channels import OutpostConsumer
from authentik.root.messages.consumer import MessageConsumer

websocket_urlpatterns = [
    path("ws/outpost/<uuid:pk>/", SentryWSMiddleware(OutpostConsumer.as_asgi())),
    path("ws/client/", AuthMiddlewareStack(SentryWSMiddleware(MessageConsumer.as_asgi()))),
]
