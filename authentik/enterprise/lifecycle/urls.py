"""API URLs"""

from authentik.enterprise.lifecycle.api.iterations import IterationViewSet
from authentik.enterprise.lifecycle.api.offboarding import UserOffboardingViewSet
from authentik.enterprise.lifecycle.api.reviews import ReviewViewSet
from authentik.enterprise.lifecycle.api.rules import LifecycleRuleViewSet

api_urlpatterns = [
    ("lifecycle/iterations", IterationViewSet),
    ("lifecycle/reviews", ReviewViewSet),
    ("lifecycle/rules", LifecycleRuleViewSet),
    ("lifecycle/user_offboarding", UserOffboardingViewSet),
]
