"""API URLs"""

from authentik.sources.ldap.api import (
    GroupLDAPSourceConnectionViewSet,
    LDAPSourcePropertyMappingViewSet,
    LDAPSourceViewSet,
    UserLDAPSourceConnectionViewSet,
)

api_urlpatterns = [
    ("propertymappings/source/ldap", LDAPSourcePropertyMappingViewSet),
    ("sources/ldap", LDAPSourceViewSet),
    ("sources/user_connections/ldap", UserLDAPSourceConnectionViewSet),
    ("sources/group_connections/ldap", GroupLDAPSourceConnectionViewSet),
]
