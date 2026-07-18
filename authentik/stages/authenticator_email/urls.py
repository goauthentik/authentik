"""API URLs"""

from authentik.stages.authenticator_email.api import (
    AuthenticatorEmailStageViewSet,
    EmailAdminDeviceViewSet,
    EmailDeviceViewSet,
)

api_urlpatterns = [
    ("authenticators/email", EmailDeviceViewSet),
    (
        "authenticators/admin/email",
        EmailAdminDeviceViewSet,
        "admin-emaildevice",
    ),
    ("stages/authenticator/email", AuthenticatorEmailStageViewSet),
]
