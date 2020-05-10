"""passbook URL Configuration"""
from django.urls import path

from passbook.core.views import authentication, overview, user
from passbook.flows.models import FlowDesignation
from passbook.flows.views import ToDefaultFlow

urlpatterns = [
    # Authentication views
    path(
        "auth/login/",
        ToDefaultFlow.as_view(designation=FlowDesignation.AUTHENTICATION),
        name="auth-login",
    ),
    path("auth/logout/", authentication.LogoutView.as_view(), name="auth-logout"),
    path(
        "auth/sign_up/",
        ToDefaultFlow.as_view(designation=FlowDesignation.ENROLLMENT),
        name="auth-sign-up",
    ),
    path(
        "auth/password/reset/<uuid:nonce_uuid>/",
        authentication.PasswordResetView.as_view(),
        name="auth-password-reset",
    ),
    # User views
    path("-/user/", user.UserSettingsView.as_view(), name="user-settings"),
    path("-/user/delete/", user.UserDeleteView.as_view(), name="user-delete"),
    path(
        "-/user/change_password/",
        user.UserChangePasswordView.as_view(),
        name="user-change-password",
    ),
    # Overview
    path("", overview.OverviewView.as_view(), name="overview"),
]
