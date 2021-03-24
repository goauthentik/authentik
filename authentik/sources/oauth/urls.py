"""authentik OAuth source urls"""

from django.urls import path

from authentik.sources.oauth.types.manager import RequestKind
from authentik.sources.oauth.views.dispatcher import DispatcherView

urlpatterns = [
    path(
        "login/<slug:source_slug>/",
        DispatcherView.as_view(kind=RequestKind.redirect),
        name="oauth-client-login",
    ),
    path(
        "callback/<slug:source_slug>/",
        DispatcherView.as_view(kind=RequestKind.callback),
        name="oauth-client-callback",
    ),
]
