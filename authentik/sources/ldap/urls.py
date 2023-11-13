"""API URLs"""
from authentik.sources.ldap.api.property_mappings import LDAPPropertyMappingViewSet
from authentik.sources.ldap.api.sources import LDAPSourceViewSet

api_urlpatterns = [
    ("propertymappings/ldap", LDAPPropertyMappingViewSet),
    ("sources/ldap", LDAPSourceViewSet),
]
