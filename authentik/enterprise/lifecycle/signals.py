"""Signal registry for the lifecycle app.

Receivers live in each feature package; importing them here connects them, as
the app framework auto-imports `<app>.signals`.
"""

from authentik.enterprise.lifecycle.review.signals import post_rule_save, pre_rule_delete

__all__ = [
    "post_rule_save",
    "pre_rule_delete",
]
