"""authentik SAML IDP URLs"""
from django.urls import path

from authentik.providers.saml.views import sso

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
]
