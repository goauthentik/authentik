"""passbook api urls"""
from django.urls import include, path

from passbook.api.v2.urls import urlpatterns as v2_urls

urlpatterns = [
    path("v2beta/", include(v2_urls)),
]
