"""API URLs"""

from authentik.enterprise.lifecycle.api.iterations import IterationViewSet
from authentik.enterprise.lifecycle.api.lifecycle_rules import LifecycleRuleViewSet
from authentik.enterprise.lifecycle.api.reviews import ReviewViewSet

api_urlpatterns = [
    ("lifecycle/lifecycle_rules", LifecycleRuleViewSet),
    ("lifecycle/iterations", IterationViewSet),
    ("lifecycle/reviews", ReviewViewSet),
]
