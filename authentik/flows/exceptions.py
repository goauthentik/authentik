"""flow exceptions"""

from django.utils.translation import gettext_lazy as _

from authentik.common.exceptions import NotReportedException
from authentik.policies.types import PolicyResult


class FlowNonApplicableException(NotReportedException):
    """Flow does not apply to current user (denied by policy, or otherwise)."""

    policy_result: PolicyResult | None = None

    @property
    def messages(self) -> str:
        """Get messages from policy result, fallback to generic reason"""
        if not self.policy_result or len(self.policy_result.messages) < 1:
            return _("Flow does not apply to current user.")
        return "\n".join(self.policy_result.messages)


class EmptyFlowException(NotReportedException):
    """Flow has no stages."""


class FlowSkipStageException(NotReportedException):
    """Exception to skip a stage"""


class StageInvalidException(NotReportedException):
    """Exception can be thrown in a `Challenge` or `ChallengeResponse` serializer's
    validation to trigger a `executor.stage_invalid()` response"""
