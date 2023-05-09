"""API URLs"""
from authentik.stages.authenticator_sms.api import (
    AuthenticatorSMSStageViewSet,
    SMSAdminDeviceViewSet,
    SMSDeviceViewSet,
)

api_urlpatterns = [
    ("authenticators/sms", SMSDeviceViewSet),
    (
        "authenticators/admin/sms",
        SMSAdminDeviceViewSet,
        "admin-smsdevice",
    ),
    ("stages/authenticator/sms", AuthenticatorSMSStageViewSet),
]
