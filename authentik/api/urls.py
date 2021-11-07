"""authentik api urls"""
from django.urls import include, path

from authentik.api.v3.urls import urlpatterns as v3_urls

urlpatterns = [
    # TODO: Remove in 2022.1
    path("v2beta/", include(v3_urls)),
    path("v3/", include(v3_urls)),
]
