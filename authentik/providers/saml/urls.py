"""authentik SAML IDP URLs"""
from django.urls import path

from authentik.providers.saml.api.property_mapping import SAMLPropertyMappingViewSet
from authentik.providers.saml.api.providers import SAMLProviderViewSet
from authentik.providers.saml.views import metadata, slo, sso

urlpatterns = [
    # SSO Bindings
    path(
        "<slug:application_slug>/sso/binding/redirect/",
        sso.SAMLSSOBindingRedirectView.as_view(),
        name="sso-redirect",
    ),
    path(
        "<slug:application_slug>/sso/binding/post/",
        sso.SAMLSSOBindingPOSTView.as_view(),
        name="sso-post",
    ),
    # SSO IdP Initiated
    path(
        "<slug:application_slug>/sso/binding/init/",
        sso.SAMLSSOBindingInitView.as_view(),
        name="sso-init",
    ),
    # SLO Bindings
    path(
        "<slug:application_slug>/slo/binding/redirect/",
        slo.SAMLSLOBindingRedirectView.as_view(),
        name="slo-redirect",
    ),
    path(
        "<slug:application_slug>/slo/binding/post/",
        slo.SAMLSLOBindingPOSTView.as_view(),
        name="slo-post",
    ),
    # Metadata
    path(
        "<slug:application_slug>/metadata/",
        metadata.MetadataDownload.as_view(),
        name="metadata-download",
    ),
]

api_urlpatterns = [
    ("propertymappings/saml", SAMLPropertyMappingViewSet),
    ("providers/saml", SAMLProviderViewSet),
]
