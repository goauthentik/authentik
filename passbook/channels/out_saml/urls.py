"""passbook SAML IDP URLs"""
from django.urls import path

from passbook.channels.out_saml import views

urlpatterns = [
    # This view is used to initiate a Login-flow from the IDP
    path(
        "<slug:application>/login/initiate/",
        views.InitiateLoginView.as_view(),
        name="saml-login-initiate",
    ),
    # This view is the endpoint a SP would redirect to, and saves data into the session
    # this is required as the process view which it redirects to might have to login first.
    path(
        "<slug:application>/login/", views.LoginBeginView.as_view(), name="saml-login"
    ),
    path(
        "<slug:application>/login/authorize/",
        views.AuthorizeView.as_view(),
        name="saml-login-authorize",
    ),
    path("<slug:application>/logout/", views.LogoutView.as_view(), name="saml-logout"),
    path(
        "<slug:application>/logout/slo/",
        views.SLOLogout.as_view(),
        name="saml-logout-slo",
    ),
    path(
        "<slug:application>/metadata/",
        views.DescriptorDownloadView.as_view(),
        name="saml-metadata",
    ),
]
