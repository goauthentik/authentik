"""passbook oauth_client urls"""

from django.urls import path

from passbook.oauth_client.source_types.manager import RequestKind
from passbook.oauth_client.views import core, dispatcher, user

urlpatterns = [
    path('login/<slug:source_slug>/', dispatcher.DispatcherView.as_view(
        kind=RequestKind.redirect), name='oauth-client-login'),
    path('callback/<slug:source_slug>/', dispatcher.DispatcherView.as_view(
        kind=RequestKind.callback), name='oauth-client-callback'),
    path('disconnect/<slug:source_slug>/', core.DisconnectView.as_view(),
         name='oauth-client-disconnect'),
    path('user/<slug:source_slug>/', user.UserSettingsView.as_view(),
         name='oauth-client-user'),
]
