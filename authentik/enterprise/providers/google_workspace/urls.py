"""google provider urls"""

from authentik.enterprise.providers.google_workspace.api.groups import (
    GoogleWorkspaceProviderGroupViewSet,
)
from authentik.enterprise.providers.google_workspace.api.property_mappings import (
    GoogleWorkspaceProviderMappingViewSet,
)
from authentik.enterprise.providers.google_workspace.api.providers import (
    GoogleWorkspaceProviderViewSet,
)
from authentik.enterprise.providers.google_workspace.api.users import (
    GoogleWorkspaceProviderUserViewSet,
)

api_urlpatterns = [
    ("providers/google_workspace", GoogleWorkspaceProviderViewSet),
    ("providers/google_workspace_users", GoogleWorkspaceProviderUserViewSet),
    ("providers/google_workspace_groups", GoogleWorkspaceProviderGroupViewSet),
    ("propertymappings/provider/google_workspace", GoogleWorkspaceProviderMappingViewSet),
]
