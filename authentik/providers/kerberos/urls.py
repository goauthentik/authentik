"""API URLs"""
from authentik.providers.kerberos.api import KerberosRealmViewSet, KerberosProviderViewSet

api_urlpatterns = [
    ("kerberos/realms", KerberosRealmViewSet),
    ("providers/kerberos", KerberosProviderViewSet),
]
