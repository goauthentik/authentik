"""google provider urls"""

from authentik.enterprise.providers.google.api.property_mappings import GoogleProviderMappingViewSet
from authentik.enterprise.providers.google.api.providers import GoogleProviderViewSet

api_urlpatterns = [
    ("providers/google", GoogleProviderViewSet),
    ("propertymappings/provider/google", GoogleProviderMappingViewSet),
]
