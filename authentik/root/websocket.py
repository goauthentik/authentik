"""root Websocket URLS"""
from channels.auth import AuthMiddleware
from channels.sessions import CookieMiddleware
from django.urls import path

from authentik.outposts.channels import OutpostConsumer
from authentik.root.asgi_middleware import SessionMiddleware
from authentik.root.messages.consumer import MessageConsumer

websocket_urlpatterns = [
    path("ws/outpost/<uuid:pk>/", OutpostConsumer.as_asgi()),
    path(
        "ws/client/", CookieMiddleware(SessionMiddleware(AuthMiddleware(MessageConsumer.as_asgi())))
    ),
]
