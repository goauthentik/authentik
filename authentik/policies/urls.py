"""API URLs"""

from django.urls import path

from authentik.policies.api.bindings import PolicyBindingViewSet
from authentik.policies.api.policies import PolicyViewSet
from authentik.policies.views import BufferView

urlpatterns = [
    path("buffer", BufferView.as_view(), name="buffer"),
]

api_urlpatterns = [
    ("policies/all", PolicyViewSet),
    ("policies/bindings", PolicyBindingViewSet),
]
