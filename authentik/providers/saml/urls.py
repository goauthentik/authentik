"""authentik SAML IDP URLs"""
from django.urls import path

from authentik.providers.saml.views import slo, sso

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
        "<slug:application_slug>/slo/redirect/",
        slo.SAMLSLOBindingRedirectView.as_view(),
        name="slo-redirect",
    ),
    path(
        "<slug:application_slug>/slo/post/",
        slo.SAMLSLOBindingPOSTView.as_view(),
        name="slo-post",
    ),
]
