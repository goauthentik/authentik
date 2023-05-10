"""API URLs"""
from authentik.policies.dummy.api import DummyPolicyViewSet

api_urlpatterns = [("policies/dummy", DummyPolicyViewSet)]
