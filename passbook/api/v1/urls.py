"""Passbook API URLs"""
from django.urls import path

from passbook.api.v1.openid import OpenIDUserInfoView

urlpatterns = [
    path('openid/', OpenIDUserInfoView.as_view(), name='openid')
]
