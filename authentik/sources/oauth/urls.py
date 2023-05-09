"""authentik OAuth source urls"""

from django.urls import path

from authentik.sources.oauth.api.source import OAuthSourceViewSet
from authentik.sources.oauth.api.source_connection import UserOAuthSourceConnectionViewSet
from authentik.sources.oauth.types.registry import RequestKind
from authentik.sources.oauth.views.dispatcher import DispatcherView

urlpatterns = [
    path(
        "login/<slug:source_slug>/",
        DispatcherView.as_view(kind=RequestKind.REDIRECT),
        name="oauth-client-login",
    ),
    path(
        "callback/<slug:source_slug>/",
        DispatcherView.as_view(kind=RequestKind.CALLBACK),
        name="oauth-client-callback",
    ),
]

api_urlpatterns = [
    ("sources/user_connections/oauth", UserOAuthSourceConnectionViewSet),
    ("sources/oauth", OAuthSourceViewSet),
]
