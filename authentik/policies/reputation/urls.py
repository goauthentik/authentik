"""API URLs"""
from authentik.policies.reputation.api import ReputationPolicyViewSet, ReputationViewSet

api_urlpatterns = [
    ("policies/reputation/scores", ReputationViewSet),
    ("policies/reputation", ReputationPolicyViewSet),
]
