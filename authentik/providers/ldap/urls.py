"""API URLs"""
from authentik.providers.ldap.api import LDAPOutpostConfigViewSet, LDAPProviderViewSet

api_urlpatterns = [
    ("outposts/ldap", LDAPOutpostConfigViewSet),
    ("providers/ldap", LDAPProviderViewSet),
]
