"""WebAuthn urls"""
from django.urls import path

from authentik.stages.authenticator_webauthn.views import UserSettingsView

urlpatterns = [
    path(
        "<uuid:stage_uuid>/settings/", UserSettingsView.as_view(), name="user-settings"
    ),
]
