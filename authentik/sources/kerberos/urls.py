"""Kerberos Source urls"""
from django.urls import path

from authentik.sources.kerberos.api.property_mapping import KerberosPropertyMappingViewSet
from authentik.sources.kerberos.api.source import KerberosSourceViewSet
from authentik.sources.kerberos.api.source_connection import UserKerberosSourceConnectionViewSet
from authentik.sources.kerberos.views import SPNEGOView

urlpatterns = [
    path("<slug:source_slug>/", SPNEGOView.as_view(), name="spnego-login"),
]

api_urlpatterns = [
    ("propertymappings/kerberos", KerberosPropertyMappingViewSet),
    ("sources/user_connections/kerberos", UserKerberosSourceConnectionViewSet),
    ("sources/kerberos", KerberosSourceViewSet),
]
