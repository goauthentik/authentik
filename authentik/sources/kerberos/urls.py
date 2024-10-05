"""Kerberos Source urls"""

from django.urls import path

from authentik.sources.kerberos.api.property_mappings import KerberosSourcePropertyMappingViewSet
from authentik.sources.kerberos.api.source import KerberosSourceViewSet
from authentik.sources.kerberos.api.source_connection import (
    GroupKerberosSourceConnectionViewSet,
    UserKerberosSourceConnectionViewSet,
)
from authentik.sources.kerberos.views import SPNEGOView

urlpatterns = [
    path("<slug:source_slug>/", SPNEGOView.as_view(), name="spnego-login"),
]

api_urlpatterns = [
    ("propertymappings/source/kerberos", KerberosSourcePropertyMappingViewSet),
    ("sources/user_connections/kerberos", UserKerberosSourceConnectionViewSet),
    ("sources/group_connections/kerberos", GroupKerberosSourceConnectionViewSet),
    ("sources/kerberos", KerberosSourceViewSet),
]
