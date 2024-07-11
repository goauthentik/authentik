"""API URLs"""

from authentik.policies.geoip.api import GeoIPPolicyViewSet

api_urlpatterns = [("policies/geoip", GeoIPPolicyViewSet)]
