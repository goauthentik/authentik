"""passbook samlv2 URLs"""
from django.urls import path

from passbook.providers.samlv2.views import idp_initiated, slo, sso

urlpatterns = [
    path(
        "<slug:application>/sso/redirect/",
        sso.SAMLRedirectBindingView.as_view(),
        name="sso-redirect",
    ),
    path(
        "<slug:application>/sso/post/",
        sso.SAMLPostBindingView.as_view(),
        name="sso-post",
    ),
    path(
        "<slug:application>/slo/redirect/",
        slo.SAMLRedirectBindingView.as_view(),
        name="slo-redirect",
    ),
    path(
        "<slug:application>/slo/redirect/",
        slo.SAMLPostBindingView.as_view(),
        name="slo-post",
    ),
    path(
        "<slug:application>/initiate/",
        idp_initiated.IDPInitiatedView.as_view(),
        name="initiate",
    ),
]
