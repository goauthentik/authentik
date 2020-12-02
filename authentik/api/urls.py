"""authentik api urls"""
from django.urls import include, path

from authentik.api.v2.urls import urlpatterns as v2_urls

urlpatterns = [
    path("v2beta/", include(v2_urls)),
]
