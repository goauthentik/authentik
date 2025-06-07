"""API URLs"""

from authentik.enterprise.api import LicenseViewSet

api_urlpatterns = [
    ("enterprise/license", LicenseViewSet),
]
