"""passbook samlv2 URLs"""
from django.urls import path

from passbook.channels.out_samlv2.views import authorize, idp_initiated, slo, sso

urlpatterns = [
    path(
        "<slug:app_slug>/authorize/",
        authorize.AuthorizeView.as_view(),
        name="authorize",
    ),
    path(
        "<slug:app_slug>/sso/redirect/",
        sso.SAMLRedirectBindingView.as_view(),
        name="sso-redirect",
    ),
    path(
        "<slug:app_slug>/sso/post/", sso.SAMLPostBindingView.as_view(), name="sso-post",
    ),
    path(
        "<slug:app_slug>/slo/redirect/",
        slo.SAMLRedirectBindingView.as_view(),
        name="slo-redirect",
    ),
    path(
        "<slug:app_slug>/slo/redirect/",
        slo.SAMLPostBindingView.as_view(),
        name="slo-post",
    ),
    path(
        "<slug:app_slug>/initiate/",
        idp_initiated.IDPInitiatedView.as_view(),
        name="initiate",
    ),
]
