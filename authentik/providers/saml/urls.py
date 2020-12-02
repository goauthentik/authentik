"""authentik SAML IDP URLs"""
from django.urls import path

from authentik.providers.saml import views

urlpatterns = [
    # SSO Bindings
    path(
        "<slug:application_slug>/sso/binding/redirect/",
        views.SAMLSSOBindingRedirectView.as_view(),
        name="sso-redirect",
    ),
    path(
        "<slug:application_slug>/sso/binding/post/",
        views.SAMLSSOBindingPOSTView.as_view(),
        name="sso-post",
    ),
    # SSO IdP Initiated
    path(
        "<slug:application_slug>/sso/binding/init/",
        views.SAMLSSOBindingInitView.as_view(),
        name="sso-init",
    ),
    path(
        "<slug:application_slug>/metadata/",
        views.DescriptorDownloadView.as_view(),
        name="metadata",
    ),
]
