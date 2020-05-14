"""passbook URL Configuration"""
from django.urls import path

from passbook.core.views import overview, user

urlpatterns = [
    # User views
    path("-/user/", user.UserSettingsView.as_view(), name="user-settings"),
    # Overview
    path("", overview.OverviewView.as_view(), name="overview"),
]
