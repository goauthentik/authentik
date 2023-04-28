"""Outpost Websocket URLS"""
from django.urls import path

from authentik.outposts.channels import OutpostConsumer
from authentik.root.middleware import ChannelsLoggingMiddleware

websocket_urlpatterns = [
    path("ws/outpost/<uuid:pk>/", ChannelsLoggingMiddleware(OutpostConsumer.as_asgi())),
]
