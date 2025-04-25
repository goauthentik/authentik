"""rac urls"""

from django.urls import path

from authentik.outposts.channels import TokenOutpostMiddleware
from authentik.providers.rac.api.connection_tokens import ConnectionTokenViewSet
from authentik.providers.rac.api.endpoints import EndpointViewSet
from authentik.providers.rac.api.property_mappings import RACPropertyMappingViewSet
from authentik.providers.rac.api.providers import RACProviderViewSet
from authentik.providers.rac.consumer_client import RACClientConsumer
from authentik.providers.rac.consumer_outpost import RACOutpostConsumer
from authentik.providers.rac.views import RACInterface, RACStartView
from authentik.root.asgi_middleware import AuthMiddlewareStack
from authentik.root.middleware import ChannelsLoggingMiddleware

urlpatterns = [
    path(
        "application/rac/<slug:app>/<uuid:endpoint>/",
        RACStartView.as_view(),
        name="start",
    ),
    path(
        "if/rac/<str:token>/",
        RACInterface.as_view(),
        name="if-rac",
    ),
]

websocket_urlpatterns = [
    path(
        "ws/rac/<str:token>/",
        ChannelsLoggingMiddleware(AuthMiddlewareStack(RACClientConsumer.as_asgi())),
    ),
    path(
        "ws/outpost_rac/<str:channel>/",
        ChannelsLoggingMiddleware(TokenOutpostMiddleware(RACOutpostConsumer.as_asgi())),
    ),
]

api_urlpatterns = [
    ("providers/rac", RACProviderViewSet),
    ("propertymappings/provider/rac", RACPropertyMappingViewSet),
    ("rac/endpoints", EndpointViewSet),
    ("rac/connection_tokens", ConnectionTokenViewSet),
]
