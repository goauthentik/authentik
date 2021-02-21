"""WebAuthn urls"""
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from authentik.stages.authenticator_webauthn.views import (
    BeginAssertion,
    UserSettingsView,
    VerifyAssertion,
)

urlpatterns = [
    path(
        "begin-assertion/",
        csrf_exempt(BeginAssertion.as_view()),
        name="assertion-begin",
    ),
    path(
        "verify-assertion/",
        csrf_exempt(VerifyAssertion.as_view()),
        name="assertion-verify",
    ),
    path(
        "<uuid:stage_uuid>/settings/", UserSettingsView.as_view(), name="user-settings"
    ),
]
