"""saml sp urls"""
from django.urls import path

from authentik.sources.saml.api.source import SAMLSourceViewSet
from authentik.sources.saml.api.source_connection import UserSAMLSourceConnectionViewSet
from authentik.sources.saml.views import ACSView, InitiateView, MetadataView, SLOView

urlpatterns = [
    path("<slug:source_slug>/", InitiateView.as_view(), name="login"),
    path("<slug:source_slug>/acs/", ACSView.as_view(), name="acs"),
    path("<slug:source_slug>/slo/", SLOView.as_view(), name="slo"),
    path("<slug:source_slug>/metadata/", MetadataView.as_view(), name="metadata"),
]

api_urlpatterns = [
    ("sources/user_connections/saml", UserSAMLSourceConnectionViewSet),
    ("sources/saml", SAMLSourceViewSet),
]
