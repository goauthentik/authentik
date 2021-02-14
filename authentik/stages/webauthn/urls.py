"""WebAuthn urls"""
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from authentik.stages.webauthn.views import (
    BeginActivateView,
    BeginAssertion,
    VerifyAssertion,
    VerifyCredentialInfo,
)

# TODO: Move to API views so we don't need csrf_exempt
urlpatterns = [
    path(
        "begin-activate/",
        csrf_exempt(BeginActivateView.as_view()),
        name="activate-begin",
    ),
    path(
        "begin-assertion/",
        csrf_exempt(BeginAssertion.as_view()),
        name="assertion-begin",
    ),
    path(
        "verify-credential-info/",
        csrf_exempt(VerifyCredentialInfo.as_view()),
        name="credential-info-verify",
    ),
    path(
        "verify-assertion/",
        csrf_exempt(VerifyAssertion.as_view()),
        name="assertion-verify",
    ),
]
