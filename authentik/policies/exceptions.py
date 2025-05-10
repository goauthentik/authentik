"""policy exceptions"""

from authentik.common.exceptions import NotReportedException


class PolicyEngineException(NotReportedException):
    """Error raised when a policy engine is configured incorrectly"""


class PolicyException(NotReportedException):
    """Exception that should be raised during Policy Evaluation, and can be recovered from."""

    src_exc: Exception | None = None

    def __init__(self, src_exc: Exception | None = None) -> None:
        super().__init__()
        self.src_exc = src_exc
