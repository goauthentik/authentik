"""WebAuthn urls"""
from django.urls import path

from authentik.stages.authenticator_webauthn.views import (
    DeviceUpdateView,
)

urlpatterns = [
    path("devices/<int:pk>/update/", DeviceUpdateView.as_view(), name="device-update"),
]
