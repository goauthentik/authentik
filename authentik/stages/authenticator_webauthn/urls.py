"""API URLs"""
from authentik.stages.authenticator_webauthn.api import (
    AuthenticateWebAuthnStageViewSet,
    WebAuthnAdminDeviceViewSet,
    WebAuthnDeviceViewSet,
)

api_urlpatterns = [
    ("stages/authenticator/webauthn", AuthenticateWebAuthnStageViewSet),
    (
        "authenticators/admin/webauthn",
        WebAuthnAdminDeviceViewSet,
        "admin-webauthndevice",
    ),
    ("authenticators/webauthn", WebAuthnDeviceViewSet),
]
