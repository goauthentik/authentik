"""API URLs"""

from django.urls import path

from authentik.enterprise.api import LicenseViewSet, SupportBundleView

api_urlpatterns = [
    ("enterprise/license", LicenseViewSet),
    path(
        "enterprise/support_bundle/", SupportBundleView.as_view(), name="enterprise_support_bundle"
    ),
]
