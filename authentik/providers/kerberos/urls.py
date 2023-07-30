"""API URLs"""
from django.urls import path

from authentik.providers.kerberos.api import (
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
]
