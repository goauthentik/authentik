"""API URLs"""

from authentik.providers.scim.api.groups import (
    SCIMProviderGroupViewSet,
)
from authentik.providers.scim.api.property_mappings import SCIMMappingViewSet
from authentik.providers.scim.api.providers import SCIMProviderViewSet
from authentik.providers.scim.api.users import (
    SCIMProviderUserViewSet,
)

api_urlpatterns = [
    ("providers/scim", SCIMProviderViewSet),
    ("providers/scim_users", SCIMProviderUserViewSet),
    ("providers/scim_groups", SCIMProviderGroupViewSet),
    ("propertymappings/provider/scim", SCIMMappingViewSet),
]
