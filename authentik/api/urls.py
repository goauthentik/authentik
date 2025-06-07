"""authentik api urls"""

from django.urls import include, path

from authentik.api.v3.urls import urlpatterns as v3_urls

urlpatterns = [
    path("v3/", include(v3_urls)),
]
