"""API URLs"""

from authentik.sources.ldap.api.connections import (
    GroupLDAPSourceConnectionViewSet,
    UserLDAPSourceConnectionViewSet,
)
from authentik.sources.ldap.api.property_mappings import LDAPSourcePropertyMappingViewSet
from authentik.sources.ldap.api.sources import LDAPSourceViewSet

api_urlpatterns = [
    ("propertymappings/source/ldap", LDAPSourcePropertyMappingViewSet),
    ("sources/ldap", LDAPSourceViewSet),
    ("sources/user_connections/ldap", UserLDAPSourceConnectionViewSet),
    ("sources/group_connections/ldap", GroupLDAPSourceConnectionViewSet),
]
