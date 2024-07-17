"""API URLs"""

from authentik.providers.radius.api.property_mappings import RadiusProviderPropertyMappingViewSet
from authentik.providers.radius.api.providers import (
    RadiusOutpostConfigViewSet,
    RadiusProviderViewSet,
)

api_urlpatterns = [
    ("propertymappings/radius", RadiusProviderPropertyMappingViewSet),
    ("outposts/radius", RadiusOutpostConfigViewSet, "radiusprovideroutpost"),
    ("providers/radius", RadiusProviderViewSet),
]
