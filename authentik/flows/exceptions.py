"""flow exceptions"""
from typing import Optional

from django.utils.translation import gettext_lazy as _

from authentik.lib.sentry import SentryIgnoredException
from authentik.policies.types import PolicyResult


class FlowNonApplicableException(SentryIgnoredException):
    """Flow does not apply to current user (denied by policy, or otherwise)."""

    policy_result: Optional[PolicyResult] = None

    @property
    def messages(self) -> str:
        """Get messages from policy result, fallback to generic reason"""
        if not self.policy_result or len(self.policy_result.messages) < 1:
            return _("Flow does not apply to current user.")
        return "\n".join(self.policy_result.messages)


class EmptyFlowException(SentryIgnoredException):
    """Flow has no stages."""


class FlowSkipStageException(SentryIgnoredException):
    """Exception to skip a stage"""


class StageInvalidException(SentryIgnoredException):
    """Exception can be thrown in a `Challenge` or `ChallengeResponse` serializer's
    validation to trigger a `executor.stage_invalid()` response"""
