"""google provider urls"""

from authentik.enterprise.providers.google_workspace.api.property_mappings import (
    GoogleProviderMappingViewSet,
)
from authentik.enterprise.providers.google_workspace.api.providers import GoogleProviderViewSet

api_urlpatterns = [
    ("providers/google_workspace", GoogleProviderViewSet),
    ("propertymappings/provider/google_workspace", GoogleProviderMappingViewSet),
]
