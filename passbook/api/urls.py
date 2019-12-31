"""passbook api urls"""
from django.urls import include, path

from passbook.api.v1.urls import urlpatterns as v1_urls
from passbook.api.v2.urls import urlpatterns as v2_urls

urlpatterns = [
    path("v1/", include(v1_urls)),
    path("v2/", include(v2_urls)),
]
