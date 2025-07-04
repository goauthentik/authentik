"""API URLs"""

from django.urls import path

from authentik.enterprise.endpoints.connectors.google_chrome.api import (
    AuthenticatorEndpointGDTCStageViewSet,
    EndpointAdminDeviceViewSet,
    EndpointDeviceViewSet,
)
from authentik.enterprise.endpoints.connectors.google_chrome.views import (
    GoogleChromeDeviceTrustConnector,
)

urlpatterns = [
    path("chrome/", GoogleChromeDeviceTrustConnector.as_view(), name="chrome"),
]
