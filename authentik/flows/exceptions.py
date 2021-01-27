"""flow exceptions"""

from authentik.lib.sentry import SentryIgnoredException


class FlowNonApplicableException(SentryIgnoredException):
    """Flow does not apply to current user (denied by policy)."""


class EmptyFlowException(SentryIgnoredException):
    """Flow has no stages."""
