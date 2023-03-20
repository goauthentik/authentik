"""Outpost Websocket URLS"""
from django.urls import path

from authentik.outposts.channels import OutpostConsumer

websocket_urlpatterns = [
    path("ws/outpost/<uuid:pk>/", OutpostConsumer.as_asgi()),
]
