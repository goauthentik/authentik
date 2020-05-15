"""passbook oauth_client urls"""

from django.urls import path

from passbook.channels.in_oauth.types.manager import RequestKind
from passbook.channels.in_oauth.views import core, dispatcher, user

urlpatterns = [
    path(
        "login/<slug:inlet_slug>/",
        dispatcher.DispatcherView.as_view(kind=RequestKind.redirect),
        name="oauth-client-login",
    ),
    path(
        "callback/<slug:inlet_slug>/",
        dispatcher.DispatcherView.as_view(kind=RequestKind.callback),
        name="oauth-client-callback",
    ),
    path(
        "disconnect/<slug:inlet_slug>/",
        core.DisconnectView.as_view(),
        name="oauth-client-disconnect",
    ),
    path(
        "user/<slug:inlet_slug>/",
        user.UserSettingsView.as_view(),
        name="oauth-client-user",
    ),
]
