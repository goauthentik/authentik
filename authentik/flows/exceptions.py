"""flow exceptions"""
from django.utils.translation import gettext_lazy as _

from authentik.lib.sentry import SentryIgnoredException
from authentik.policies.types import PolicyResult


class FlowNonApplicableException(SentryIgnoredException):
    """Flow does not apply to current user (denied by policy)."""

    policy_result: PolicyResult

    @property
    def messages(self) -> str:
        """Get messages from policy result, fallback to generic reason"""
        if len(self.policy_result.messages) < 1:
            return _("Flow does not apply to current user (denied by policy).")
        return "\n".join(self.policy_result.messages)


class EmptyFlowException(SentryIgnoredException):
    """Flow has no stages."""


class FlowSkipStageException(SentryIgnoredException):
    """Exception to skip a stage"""
