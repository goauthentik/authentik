"""API URLs"""
from authentik.sources.ldap.api import LDAPPropertyMappingViewSet, LDAPSourceViewSet

api_urlpatterns = [
    ("propertymappings/ldap", LDAPPropertyMappingViewSet),
    ("sources/ldap", LDAPSourceViewSet),
]
