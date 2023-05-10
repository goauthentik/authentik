"""API URLs"""
from authentik.policies.event_matcher.api import EventMatcherPolicyViewSet

api_urlpatterns = [("policies/event_matcher", EventMatcherPolicyViewSet)]
