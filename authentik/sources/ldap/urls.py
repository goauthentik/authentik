"""API URLs"""

from authentik.sources.ldap.api import LDAPSourcePropertyMappingViewSet, LDAPSourceViewSet

api_urlpatterns = [
    ("propertymappings/ldap", LDAPSourcePropertyMappingViewSet),
    ("sources/ldap", LDAPSourceViewSet),
]
