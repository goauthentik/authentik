"""Managed secret signals."""

from django.dispatch import Signal

# Sent with `secret` and the proposed `value` before an existing secret's value changes.
# Receivers raise ValidationError when a consumer can't use the value.
secret_value_validating = Signal()
# Sent with `secret` after its value changed, inside the transaction.
secret_value_changed = Signal()
secret_value_validating = Signal()
