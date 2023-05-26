"""API URLs"""
from authentik.sources.ldap.api.sources import LDAPSourceViewSet
from authentik.sources.ldap.api.property_mappings import LDAPPropertyMappingViewSet
from authentik.sources.ldap.api.source_connections import LDAPUserSourceConnectionViewSet

api_urlpatterns = [
    ("propertymappings/ldap", LDAPPropertyMappingViewSet),
    ("sources/user_connections/ldap", LDAPUserSourceConnectionViewSet),
    ("sources/ldap", LDAPSourceViewSet),
]
