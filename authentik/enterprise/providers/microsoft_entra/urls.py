"""microsoft provider urls"""

from authentik.enterprise.providers.microsoft_entra.api.property_mappings import (
    MicrosoftEntraProviderMappingViewSet,
)
from authentik.enterprise.providers.microsoft_entra.api.providers import (
    MicrosoftEntraProviderViewSet,
)

api_urlpatterns = [
    ("providers/microsoft_entra", MicrosoftEntraProviderViewSet),
    ("propertymappings/provider/microsoft_entra", MicrosoftEntraProviderMappingViewSet),
]
