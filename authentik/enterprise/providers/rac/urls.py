"""rac urls"""

from channels.auth import AuthMiddleware
from channels.sessions import CookieMiddleware
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie

from authentik.enterprise.providers.rac.api.connection_tokens import ConnectionTokenViewSet
from authentik.enterprise.providers.rac.api.endpoints import EndpointViewSet
from authentik.enterprise.providers.rac.api.property_mappings import RACPropertyMappingViewSet
from authentik.enterprise.providers.rac.api.providers import RACProviderViewSet
from authentik.enterprise.providers.rac.consumer_client import RACClientConsumer
from authentik.enterprise.providers.rac.consumer_outpost import RACOutpostConsumer
from authentik.enterprise.providers.rac.views import RACInterface, RACStartView
from authentik.outposts.channels import TokenOutpostMiddleware
from authentik.root.asgi_middleware import SessionMiddleware
from authentik.root.middleware import ChannelsLoggingMiddleware

urlpatterns = [
    path(
        "application/rac/<slug:app>/<uuid:endpoint>/",
        ensure_csrf_cookie(RACStartView.as_view()),
        name="start",
    ),
    path(
        "if/rac/<str:token>/",
        ensure_csrf_cookie(RACInterface.as_view()),
        name="if-rac",
    ),
]

websocket_urlpatterns = [
    path(
        "ws/rac/<str:token>/",
        ChannelsLoggingMiddleware(
            CookieMiddleware(SessionMiddleware(AuthMiddleware(RACClientConsumer.as_asgi())))
        ),
    ),
    path(
        "ws/outpost_rac/<str:channel>/",
        ChannelsLoggingMiddleware(TokenOutpostMiddleware(RACOutpostConsumer.as_asgi())),
    ),
]

api_urlpatterns = [
    ("providers/rac", RACProviderViewSet),
    ("propertymappings/rac", RACPropertyMappingViewSet),
    ("rac/endpoints", EndpointViewSet),
    ("rac/connection_tokens", ConnectionTokenViewSet),
]
