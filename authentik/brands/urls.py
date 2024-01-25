"""API URLs"""
from authentik.brands.api import BrandViewSet

api_urlpatterns = [
    ("core/brands", BrandViewSet),
]
