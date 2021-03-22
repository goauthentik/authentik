"""authentik api urls"""
from django.urls import include, path
from django.views.i18n import JavaScriptCatalog

from authentik.api.v2.urls import urlpatterns as v2_urls

urlpatterns = [
    path("v2beta/", include(v2_urls)),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
]
