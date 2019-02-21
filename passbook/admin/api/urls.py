"""Versioned Admin API Urls"""
from django.conf.urls import include, url

urlpatterns = [
    url(r'^v1/', include('passbook.admin.api.v1.urls', namespace='v1')),
]
