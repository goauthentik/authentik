"""saml sp urls"""
from django.urls import path

from passbook.sources.saml.views import ACSView, InitiateView, MetadataView, SLOView

urlpatterns = [
    path("<slug:source>/", InitiateView.as_view(), name="login"),
    path("<slug:source>/acs/", ACSView.as_view(), name="acs"),
    path("<slug:source>/slo/", SLOView.as_view(), name="slo"),
    path("<slug:source>/metadata/", MetadataView.as_view(), name="metadata"),
]
