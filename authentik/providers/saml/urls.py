"""authentik SAML IDP URLs"""
from django.urls import path

from authentik.providers.saml.views import metadata, sso

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
    path(
        "<slug:application_slug>/metadata/",
        metadata.DescriptorDownloadView.as_view(),
        name="metadata",
    ),
]
