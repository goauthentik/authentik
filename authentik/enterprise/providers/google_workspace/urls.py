"""google provider urls"""

from authentik.enterprise.providers.google_workspace.api.property_mappings import (
    GoogleWorkspaceProviderMappingViewSet,
)
from authentik.enterprise.providers.google_workspace.api.providers import (
    GoogleWorkspaceProviderViewSet,
)

api_urlpatterns = [
    ("providers/google_workspace", GoogleWorkspaceProviderViewSet),
    ("propertymappings/provider/google_workspace", GoogleWorkspaceProviderMappingViewSet),
]
