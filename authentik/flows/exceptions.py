"""flow exceptions"""

from authentik.lib.sentry import SentryIgnoredException
from authentik.policies.types import PolicyResult


class FlowNonApplicableException(SentryIgnoredException):
    """Flow does not apply to current user (denied by policy)."""

    policy_result: PolicyResult


class EmptyFlowException(SentryIgnoredException):
    """Flow has no stages."""


class FlowSkipStageException(SentryIgnoredException):
    """Exception to skip a stage"""
