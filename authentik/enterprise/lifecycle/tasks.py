"""Task registry for the lifecycle app.

Actors live in each feature package; importing them here registers them, as the
app framework auto-imports `<app>.tasks`.
"""

from authentik.enterprise.lifecycle.offboarding.tasks import (
    execute_due_offboardings,
    execute_offboarding,
)
from authentik.enterprise.lifecycle.review.tasks import (
    apply_lifecycle_rule,
    apply_lifecycle_rules,
    send_notification,
)

__all__ = [
    "apply_lifecycle_rule",
    "apply_lifecycle_rules",
    "execute_due_offboardings",
    "execute_offboarding",
    "send_notification",
]
