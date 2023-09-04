"""API URLs"""
from authentik.stages.authenticator_mobile.api.device import (
    AdminMobileDeviceViewSet,
    MobileDeviceViewSet,
)
from authentik.stages.authenticator_mobile.api.stage import AuthenticatorMobileStageViewSet
from rest_framework import routers

# Separate router which is used for the subset-schema generation
# for the cloud-gateway we (currently) only want the mobile device endpoints
# and don't need all other API endpoints
router = routers.DefaultRouter()
router.register("authenticators/mobile", MobileDeviceViewSet)

api_urlpatterns = [
    ("authenticators/mobile", MobileDeviceViewSet),
    (
        "authenticators/admin/mobile",
        AdminMobileDeviceViewSet,
        "admin-mobiledevice",
    ),
    ("stages/authenticator/mobile", AuthenticatorMobileStageViewSet),
]

urlpatterns = router.urls
