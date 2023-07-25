"""API URLs"""
from authentik.stages.authenticator_mobile.api.device import (
    AdminMobileDeviceViewSet,
    MobileDeviceViewSet,
)
from authentik.stages.authenticator_mobile.api.stage import AuthenticatorMobileStageViewSet

api_urlpatterns = [
    ("authenticators/mobile", MobileDeviceViewSet),
    (
        "authenticators/admin/mobile",
        AdminMobileDeviceViewSet,
        "admin-mobiledevice",
    ),
    ("stages/authenticator/mobile", AuthenticatorMobileStageViewSet),
]
