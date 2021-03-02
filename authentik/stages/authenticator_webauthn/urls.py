"""WebAuthn urls"""
from django.urls import path

from authentik.stages.authenticator_webauthn.views import (
    DeviceDeleteView,
    DeviceUpdateView,
    UserSettingsView,
)

urlpatterns = [
    path(
        "<uuid:stage_uuid>/settings/", UserSettingsView.as_view(), name="user-settings"
    ),
    path("devices/<int:pk>/delete/", DeviceDeleteView.as_view(), name="device-delete"),
    path("devices/<int:pk>/update/", DeviceUpdateView.as_view(), name="device-update"),
]
