"""root Websocket URLS"""
from channels.auth import AuthMiddlewareStack
from django.urls import path

from authentik.outposts.channels import OutpostConsumer
from authentik.root.messages.consumer import MessageConsumer

websocket_urlpatterns = [
    path("ws/outpost/<uuid:pk>/", OutpostConsumer.as_asgi()),
    path("ws/client/", AuthMiddlewareStack(MessageConsumer.as_asgi())),
]
