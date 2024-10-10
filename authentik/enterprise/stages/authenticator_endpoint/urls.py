"""API URLs"""

from django.urls import path

from authentik.enterprise.stages.authenticator_endpoint.api import (
    AuthenticatorEndpointStageViewSet,
    EndpointAdminDeviceViewSet,
    EndpointDeviceViewSet,
)
from authentik.enterprise.stages.authenticator_endpoint.views.google_chrome.dtc import (
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
    ("stages/authenticator/endpoint", AuthenticatorEndpointStageViewSet),
]
