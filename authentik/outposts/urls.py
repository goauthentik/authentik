"""Outpost Websocket URLS"""
from django.urls import path

from authentik.outposts.api.outposts import OutpostViewSet
from authentik.outposts.api.service_connections import (
    DockerServiceConnectionViewSet,
    KubernetesServiceConnectionViewSet,
    ServiceConnectionViewSet,
)
from authentik.outposts.channels import OutpostConsumer
from authentik.root.middleware import ChannelsLoggingMiddleware

websocket_urlpatterns = [
    path("ws/outpost/<uuid:pk>/", ChannelsLoggingMiddleware(OutpostConsumer.as_asgi())),
]

api_urlpatterns = [
    ("outposts/instances", OutpostViewSet),
    ("outposts/service_connections/all", ServiceConnectionViewSet),
    ("outposts/service_connections/docker", DockerServiceConnectionViewSet),
    ("outposts/service_connections/kubernetes", KubernetesServiceConnectionViewSet),
]
