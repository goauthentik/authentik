"""API URLs"""
from authentik.stages.authenticator_duo.api import (
    AuthenticatorDuoStageViewSet,
    DuoAdminDeviceViewSet,
    DuoDeviceViewSet,
)

api_urlpatterns = [
    ("authenticators/duo", DuoDeviceViewSet),
    (
        "authenticators/admin/duo",
        DuoAdminDeviceViewSet,
        "admin-duodevice",
    ),
    ("stages/authenticator/duo", AuthenticatorDuoStageViewSet),
]
