"""API URLs"""
from django.urls import path

from authentik.providers.kerberos.api.property_mapping import KerberosPrincipalMappingViewSet
from authentik.providers.kerberos.api.provider import (
    KerberosOutpostConfigViewSet,
    KerberosProviderViewSet,
    KerberosRealmViewSet,
)
from authentik.providers.kerberos.views import KdcProxyView

urlpatterns = [
    path("<str:realm_name>/proxy/", KdcProxyView.as_view(), name="kdc-proxy"),
]

api_urlpatterns = [
    ("outposts/kerberos", KerberosOutpostConfigViewSet, "kerberosrealmoutpost"),
    ("providers/kerberos/realms", KerberosRealmViewSet),
    ("providers/kerberos", KerberosProviderViewSet),
    ("propertymappings/kerberosprincipal", KerberosPrincipalMappingViewSet),
]
