"""API URLs"""

from django.urls import path

from authentik.policies.geoip.api import GeoIPPolicyViewSet
from authentik.policies.geoip.views import ISO3166View

api_urlpatterns = [
    ("policies/geoip", GeoIPPolicyViewSet),
    path("policies/geoip_iso3166/", ISO3166View.as_view(), name="iso-3166-view"),
]
