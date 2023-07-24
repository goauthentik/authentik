"""API URLs"""
from authentik.stages.authenticator_mobile.api import (
    AdminMobileDeviceViewSet,
    AuthenticatorMobileStageViewSet,
    MobileDeviceViewSet,
)

api_urlpatterns = [
    ("authenticators/mobile", MobileDeviceViewSet),
    (
        "authenticators/admin/mobile",
        AdminMobileDeviceViewSet,
        "admin-mobiledevice",
    ),
    ("stages/authenticator/mobile", AuthenticatorMobileStageViewSet),
]
