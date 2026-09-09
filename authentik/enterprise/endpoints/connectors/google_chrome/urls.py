"""API URLs"""

from django.urls import path

from authentik.enterprise.endpoints.connectors.google_chrome.api import GoogleChromeConnectorViewSet
from authentik.enterprise.endpoints.connectors.google_chrome.views.dtc import (
    GoogleChromeDeviceTrustConnector,
)

urlpatterns = [
    path("chrome/", GoogleChromeDeviceTrustConnector.as_view(), name="chrome"),
]

api_urlpatterns = [
    ("endpoints/google_chrome/connectors", GoogleChromeConnectorViewSet),
]
