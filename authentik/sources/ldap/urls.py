"""API URLs"""

from authentik.sources.ldap.api import LDAPSourcePropertyMappingViewSet, LDAPSourceViewSet

api_urlpatterns = [
    ("propertymappings/source/ldap", LDAPSourcePropertyMappingViewSet),
    ("sources/ldap", LDAPSourceViewSet),
]
