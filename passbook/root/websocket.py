"""root Websocket URLS"""
from channels.auth import AuthMiddlewareStack
from django.urls import path

from passbook.outposts.channels import OutpostConsumer
from passbook.root.messages.consumer import MessageConsumer

websocket_urlpatterns = [
    path("ws/outpost/<uuid:pk>/", OutpostConsumer.as_asgi()),
    path("ws/client/", AuthMiddlewareStack(MessageConsumer.as_asgi())),
]
