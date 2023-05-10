"""API URLs"""
from authentik.stages.authenticator_static.api import (
    AuthenticatorStaticStageViewSet,
    StaticAdminDeviceViewSet,
    StaticDeviceViewSet,
)

api_urlpatterns = [
    ("authenticators/static", StaticDeviceViewSet),
    (
        "authenticators/admin/static",
        StaticAdminDeviceViewSet,
        "admin-staticdevice",
    ),
    ("stages/authenticator/static", AuthenticatorStaticStageViewSet),
]
