"""API URLs"""
from authentik.enterprise.lifecycle.api.attestations import AttestationViewSet
from authentik.enterprise.lifecycle.api.lifecycle_rules import LifecycleRuleViewSet
from authentik.enterprise.lifecycle.api.reviews import ReviewViewSet

api_urlpatterns = [
    ("lifecycle/lifecycle_rules", LifecycleRuleViewSet),
    ("lifecycle/reviews", ReviewViewSet),
    ("lifecycle/attestations", AttestationViewSet),
]
