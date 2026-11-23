"""Signal registry for the lifecycle app.

Receivers live in each feature package; importing them here connects them, as
the app framework auto-imports `<app>.signals`.
"""

from authentik.enterprise.lifecycle.expiration.signals import (
    expiration_on_user_logged_in,
    expiration_on_user_save,
    expiration_post_rule_save,
    expiration_pre_rule_delete,
)
from authentik.enterprise.lifecycle.review.signals import post_rule_save, pre_rule_delete

__all__ = [
    "expiration_on_user_logged_in",
    "expiration_on_user_save",
    "expiration_post_rule_save",
    "expiration_pre_rule_delete",
    "post_rule_save",
    "pre_rule_delete",
]
