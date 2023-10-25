"""rac urls"""
from channels.auth import AuthMiddleware
from channels.sessions import CookieMiddleware
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie

from authentik.core.channels import TokenOutpostMiddleware
from authentik.enterprise.providers.rac.api.providers import RACProviderViewSet
from authentik.enterprise.providers.rac.consumer_client import RACClientConsumer
from authentik.enterprise.providers.rac.consumer_outpost import RACOutpostConsumer
from authentik.enterprise.providers.rac.views import RACInterface
from authentik.root.asgi_middleware import SessionMiddleware
from authentik.root.middleware import ChannelsLoggingMiddleware

urlpatterns = [
    path(
        "if/rac/<slug:app>/",
        ensure_csrf_cookie(RACInterface.as_view()),
        name="if-rac",
    ),
]

websocket_urlpatterns = [
    path(
        "ws/rac/<slug:app>/",
        CookieMiddleware(SessionMiddleware(AuthMiddleware(RACClientConsumer.as_asgi()))),
    ),
    path(
        "ws/outpost_rac/<str:channel>/",
        ChannelsLoggingMiddleware(TokenOutpostMiddleware(RACOutpostConsumer.as_asgi())),
    ),
]

api_urlpatterns = [
    ("providers/rac", RACProviderViewSet),
]
