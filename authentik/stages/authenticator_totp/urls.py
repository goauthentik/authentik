"""API URLs"""
from authentik.stages.authenticator_totp.api import (
    AuthenticatorTOTPStageViewSet,
    TOTPAdminDeviceViewSet,
    TOTPDeviceViewSet,
)

api_urlpatterns = [
    ("authenticators/totp", TOTPDeviceViewSet),
    ("authenticators/admin/totp", TOTPAdminDeviceViewSet, "admin-totpdevice"),
    ("stages/authenticator/totp", AuthenticatorTOTPStageViewSet),
]
