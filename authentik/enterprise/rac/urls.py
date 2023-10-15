"""rac urls"""
from channels.auth import AuthMiddleware
from channels.sessions import CookieMiddleware
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie

from authentik.core.views.interface import InterfaceView
from authentik.enterprise.rac.api.providers import RACProviderViewSet
from authentik.enterprise.rac.consumer_client import RACClientConsumer
from authentik.enterprise.rac.consumer_outpost import RACOutpostConsumer
from authentik.root.asgi_middleware import SessionMiddleware
from authentik.root.middleware import ChannelsLoggingMiddleware

urlpatterns = [
    path(
        "if/rac/<slug:app>/",
        ensure_csrf_cookie(InterfaceView.as_view(template_name="if/rac.html")),
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
        ChannelsLoggingMiddleware(RACOutpostConsumer.as_asgi()),
    ),
]

api_urlpatterns = [
    ("providers/enterprise/rac", RACProviderViewSet),
]
