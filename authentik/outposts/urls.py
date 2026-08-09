"""Outpost Websocket URLS"""

from django.urls import path

from authentik.outposts.api.outposts import OutpostViewSet
from authentik.outposts.api.service_connections import (
    DockerServiceConnectionViewSet,
    KubernetesServiceConnectionViewSet,
    ServiceConnectionViewSet,
)
from authentik.outposts.channels import TokenOutpostMiddleware
from authentik.outposts.consumer import OutpostConsumer
from authentik.root.middleware import ChannelsLoggingMiddleware
from authentik.tenants.channels import TenantsAwareMiddleware

websocket_urlpatterns = [
    path(
        "ws/outpost/<uuid:pk>/",
        ChannelsLoggingMiddleware(
            TenantsAwareMiddleware(TokenOutpostMiddleware(OutpostConsumer.as_asgi()))
        ),
    ),
]

api_urlpatterns = [
    ("outposts/instances", OutpostViewSet),
    ("outposts/service_connections/all", ServiceConnectionViewSet),
    ("outposts/service_connections/docker", DockerServiceConnectionViewSet),
    ("outposts/service_connections/kubernetes", KubernetesServiceConnectionViewSet),
]
