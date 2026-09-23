"""Model registry for the lifecycle app.

The lifecycle app is an umbrella for sibling features that each live in their
own package: `review/` (object access reviews) and `offboarding/` (user
offboarding). Django loads models through this module, so every feature's
models must be imported here.
"""

# Import order sets model registration order, which the API schema's ModelEnum
# follows; review stays first to match the pre-split layout.
# isort: off
from authentik.enterprise.lifecycle.review.models import (
    LifecycleIteration,
    LifecycleRule,
    LifecycleRuleNotificationTransport,
    LifecycleRuleReviewer,
    LifecycleRuleReviewerGroup,
    Review,
    ReviewState,
)
from authentik.enterprise.lifecycle.offboarding.models import (
    OffboardingAction,
    OffboardingStatus,
    UserOffboarding,
)

# isort: on

__all__ = [
    "LifecycleIteration",
    "LifecycleRule",
    "LifecycleRuleNotificationTransport",
    "LifecycleRuleReviewer",
    "LifecycleRuleReviewerGroup",
    "OffboardingAction",
    "OffboardingStatus",
    "Review",
    "ReviewState",
    "UserOffboarding",
]
