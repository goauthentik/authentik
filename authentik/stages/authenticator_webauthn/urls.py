"""API URLs"""

from authentik.stages.authenticator_webauthn.api.device_types import WebAuthnDeviceTypeViewSet
from authentik.stages.authenticator_webauthn.api.devices import (
    WebAuthnAdminDeviceViewSet,
    WebAuthnDeviceViewSet,
)
from authentik.stages.authenticator_webauthn.api.rp_configs import WebAuthnRPConfigViewSet
from authentik.stages.authenticator_webauthn.api.stages import AuthenticatorWebAuthnStageViewSet

api_urlpatterns = [
    ("stages/authenticator/webauthn", AuthenticatorWebAuthnStageViewSet),
    ("stages/authenticator/webauthn_device_types", WebAuthnDeviceTypeViewSet),
    ("stages/authenticator/webauthn_rp_configs", WebAuthnRPConfigViewSet),
    (
        "authenticators/admin/webauthn",
        WebAuthnAdminDeviceViewSet,
        "admin-webauthndevice",
    ),
    ("authenticators/webauthn", WebAuthnDeviceViewSet),
]
