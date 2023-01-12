"""rac urls"""
from channels.auth import AuthMiddleware
from channels.sessions import CookieMiddleware
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie

from authentik.core.views.interface import InterfaceView
from authentik.enterprise.rac.api.providers import RACProviderViewSet
from authentik.enterprise.rac.consumer import GuacamoleConsumer
from authentik.root.asgi_middleware import SessionMiddleware

urlpatterns = [
    path(
        "if/rac/",
        ensure_csrf_cookie(InterfaceView.as_view(template_name="if/rac.html")),
        name="if-rac",
    ),
]

websocket_urlpatterns = [
    path(
        "ws/rac/<slug:app>/",
        CookieMiddleware(SessionMiddleware(AuthMiddleware(GuacamoleConsumer.as_asgi()))),
    ),
]

api_urlpatterns = [
    ("providers/enterprise/rac", RACProviderViewSet),
]
