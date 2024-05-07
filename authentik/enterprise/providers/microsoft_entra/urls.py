"""microsoft provider urls"""

from authentik.enterprise.providers.microsoft_entra.api.property_mappings import (
    MicrosoftProviderMappingViewSet,
)
from authentik.enterprise.providers.microsoft_entra.api.providers import MicrosoftProviderViewSet

api_urlpatterns = [
    ("providers/microsoft_entra", MicrosoftProviderViewSet),
    ("propertymappings/provider/microsoft_entra", MicrosoftProviderMappingViewSet),
]
