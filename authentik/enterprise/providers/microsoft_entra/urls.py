"""microsoft provider urls"""

from authentik.enterprise.providers.microsoft_entra.api.groups import (
    MicrosoftEntraProviderGroupViewSet,
)
from authentik.enterprise.providers.microsoft_entra.api.property_mappings import (
    MicrosoftEntraProviderMappingViewSet,
)
from authentik.enterprise.providers.microsoft_entra.api.providers import (
    MicrosoftEntraProviderViewSet,
)
from authentik.enterprise.providers.microsoft_entra.api.users import (
    MicrosoftEntraProviderUserViewSet,
)

api_urlpatterns = [
    ("providers/microsoft_entra", MicrosoftEntraProviderViewSet),
    ("providers/microsoft_entra_users", MicrosoftEntraProviderUserViewSet),
    ("providers/microsoft_entra_groups", MicrosoftEntraProviderGroupViewSet),
    ("propertymappings/provider/microsoft_entra", MicrosoftEntraProviderMappingViewSet),
]
