"""API URLs"""
from authentik.enterprise.reviews.api.attestations import AttestationViewSet
from authentik.enterprise.reviews.api.lifecycle_rules import LifecycleRuleViewSet
from authentik.enterprise.reviews.api.reviews import ReviewViewSet

api_urlpatterns = [
    ("reviews/lifecycle_rules", LifecycleRuleViewSet),
    ("reviews/reviews", ReviewViewSet),
    ("reviews/attestations", AttestationViewSet),
]
