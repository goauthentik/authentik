"""API URLs"""
from authentik.providers.kerberos.api import KerberosProviderViewSet, KerberosRealmViewSet

api_urlpatterns = [
    ("kerberos/realms", KerberosRealmViewSet),
    ("providers/kerberos", KerberosProviderViewSet),
]
