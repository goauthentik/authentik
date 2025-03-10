"""API URLs"""

from django.urls import path

from authentik.enterprise.stages.authenticator_endpoint_gdtc.api import (
    AuthenticatorEndpointGDTCStageViewSet,
    EndpointAdminDeviceViewSet,
    EndpointDeviceViewSet,
)
from authentik.enterprise.stages.authenticator_endpoint_gdtc.views.dtc import (
    GoogleChromeDeviceTrustConnector,
)

urlpatterns = [
    path("chrome/", GoogleChromeDeviceTrustConnector.as_view(), name="chrome"),
]

api_urlpatterns = [
    ("authenticators/endpoint", EndpointDeviceViewSet),
    (
        "authenticators/admin/endpoint",
        EndpointAdminDeviceViewSet,
        "admin-endpointdevice",
    ),
    ("stages/authenticator/endpoint_gdtc", AuthenticatorEndpointGDTCStageViewSet),
]
