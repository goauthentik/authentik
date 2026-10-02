"""API URLs"""

from authentik.enterprise.lifecycle.offboarding.api import UserOffboardingViewSet
from authentik.enterprise.lifecycle.review.api.iterations import IterationViewSet
from authentik.enterprise.lifecycle.review.api.reviews import ReviewViewSet
from authentik.enterprise.lifecycle.review.api.rules import LifecycleRuleViewSet

api_urlpatterns = [
    ("lifecycle/iterations", IterationViewSet),
    ("lifecycle/reviews", ReviewViewSet),
    ("lifecycle/rules", LifecycleRuleViewSet),
    ("lifecycle/user_offboarding", UserOffboardingViewSet),
]
