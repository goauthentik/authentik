"""API URLs"""

from authentik.sources.ldap.api import LDAPSourcePropertyMappingViewSet, LDAPSourceViewSet

api_urlpatterns = [
    ("propertymappings/ldapsource", LDAPSourcePropertyMappingViewSet),
    ("sources/ldap", LDAPSourceViewSet),
]
