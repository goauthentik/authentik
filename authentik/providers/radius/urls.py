"""API URLs"""
from authentik.providers.radius.api import RadiusOutpostConfigViewSet, RadiusProviderViewSet

api_urlpatterns = [
    ("outposts/radius", RadiusOutpostConfigViewSet),
    ("providers/radius", RadiusProviderViewSet),
]
