"""API URLs"""
from authentik.policies.api.bindings import PolicyBindingViewSet
from authentik.policies.api.policies import PolicyViewSet

api_urlpatterns = [
    ("policies/all", PolicyViewSet),
    ("policies/bindings", PolicyBindingViewSet),
]
