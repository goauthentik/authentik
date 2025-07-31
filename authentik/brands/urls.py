"""API URLs"""

from authentik.brands.api import BrandPolicyViewSet, BrandViewSet

api_urlpatterns = [
    ("core/brands", BrandViewSet),
    ("core/brand_policies", BrandPolicyViewSet),
]
